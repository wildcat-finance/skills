# ADR-028: Continue Fiat only from resumable checkpoints

## Status

Accepted, 2026-08-27, at the Creator's direction. This decision replaces the
portable-checkpoint service proposal previously recorded here and retires
ADR-029 through ADR-032.

Corrected, 2026-08-27: audit continuation starts a new bounded audit loop on
the same ledger. It never raises one loop's round ceiling or continues that
loop as round 9.

Amended, 2026-08-29: Fiat owns a checked controller-state capsule and
same-ledger relocation. The standing outer transport and semantic identity
remain separate concerns.

Amended, 2026-08-29: future Fiat runs resolve one immutable starting commit
at initialization and bind it through an init-owned run anchor. Semantic
checkpoint identity is separate from exact capsule and archive bytes.

Amended, 2026-08-30: every accepted boundary now produces an unconditional
local archive in the origin checkout. Drive publication, issue-note publication
and the checkpoint waiver are retired. Until a distributed transport is
accepted, agents pass the local path and digests directly to one another.

## Context

Fiat's controller state and receipt ledger live under the run worktree's
ignored `.hexaemeron/` directory. Git preserves committed product history, but
it cannot reconstruct the controller's exact run identity, receipt prefix,
audit history, halt state, or next permitted action.

Earlier continuation attempts copied product evidence into a newly initialised
Fiat run and called that process inoculation. That starts a different ledger.
It may preserve useful evidence, but it does not continue the run that earned
the receipts. The service, authority, object-lock and lineage proposals that
grew around that model also made a local recovery rule depend on infrastructure
that does not exist.

The practical requirement is narrower: preserve the exact controller state
when a run reaches a useful stopping boundary, then let another agent continue
the same run from the next controller directive.

## Decision

Fiat continuation uses checkpoints only. A continuation restores the same
run, controller state and ledger; it never calls `init`, starts a fresh ledger,
replays study or runbook receipts, or inoculates a new run with old evidence.

A checkpoint is created at exactly two boundaries:

1. **Successful end of step.** The step's `done push` receipt succeeded, the
   committed step head is signed and remotely verified, and no later directive
   has been acted on.
2. **Exhausted audit.** The final allowed audit round is receipted with findings
   still open and `next` returns `audit-verdict`. This boundary is deliberately
   finding-bearing and non-green.

Arbitrary mid-phase snapshots are not continuation checkpoints.

The checkpoint preserves:

- the complete `.hexaemeron` directory, excluding only the transient lock;
- a Git bundle containing the run base, run branch, step branches and every
  object needed by the recorded working commit;
- the exact state and ledger bytes, their digests, the run and controller
  identity, the recorded ref boundary, and the expected next directive;
- the public key and bounded proof needed to verify signed run commits; and
- a sorted recursive SHA-256 inventory of the copied controller state.

Every accepted boundary is packaged locally under the origin checkout:

```text
<origin>/.hexaemeron/checkpoints/<run-worktree-name>/
  step-<n>-<full-head-sha>/
  audit-verdict-step-<n>-loop-<loop>-<full-head-sha>/
```

The path is derived from controller state. It is not chosen by the user. Each
new boundary directory holds the checkpoint zip and its outer SHA-256 sidecar;
the zip holds the controller capsule, Git bundle, outer manifest, public key,
signature proof, member sidecars and restore README. The final directory is
exposed only after the archive and sidecar verify, and an existing checkpoint
is never replaced.

Checkpointing is unconditional. No run direction waives it, and an agent never
asks the user whether to save it, where it should go, or whether it should be
kept. A failed save blocks the next directive until the same boundary is
preserved successfully. Checkpointing performs no upload, issue comment,
commit or push.

Until a distributed checkpoint framework is accepted, transfer is a direct
local agent-to-agent hand-off. The producer passes the absolute archive path,
outer and controller-manifest digests, run and boundary identity, full head SHA
and expected directive. The receiver verifies those values, the archive,
bundle, signatures and controller capsule before restoring the same ledger.

Every restore starts inside the preserved run worktree with:

```text
hexctl verify
hexctl status
hexctl next
```

The restored state is canonical. Act only on the directive `next` returns.

Audit history is two-dimensional: audit loop, then round within that loop. Each
loop starts at round 1 and may contain at most eight rounds. The first eight
rounds already recorded by a legacy state are loop 1.

An exhausted loop remains halted until the user authorises another loop. The
exhausted-loop checkpoint is created before that transition. A checked
controller transition then appends a new loop to the same step and ledger,
binding the new loop to the predecessor checkpoint, the open-finding set and
the user's authorisation. The prior loop is immutable. `next` must return
`audit-round` with the new loop identity and round 1.

`audit.max_rounds` is a per-loop ceiling. It is never raised to simulate
another loop, and round numbering never continues as 9, 10 or beyond. Starting
a new loop does not accept or close any inherited finding. A controller that
does not yet implement the checked new-loop transition must leave the run
halted at its exhausted checkpoint.

Historical archives, issue comments and filenames that use `carryover` or
`inoculation` remain evidence of what happened. They do not authorise that
procedure for a current continuation.

## Amendment: Native controller-state relocation (2026-08-29)

Fiat exports the complete controller tree at either accepted boundary as a
bounded directory using schema `fiat-controller-checkpoint/v1`. Its manifest
binds the sorted file inventory, state and ledger digests, ledger tail,
controller identity, exact local Git ref boundary and expected next directive.
The capsule carries no source path, timestamp, credential, acceptance claim or
service receipt.

Restore begins in a fresh checkout where the declared Git refs have already
been restored and verified. It verifies the capsule and ref boundary before it
creates active state. The imported ledger remains an exact prefix. Fiat changes
only the imported origin and worktree locations, appends one
`checkpoint:restore` receipt to the same ledger, recreates the breadcrumb, and
checks `verify`, `status` and `next`. It does not execute the returned
directive.

The capsule's manifest digest identifies exact controller bytes. It is not the
semantic checkpoint identity, acceptance receipt or deterministic outer
archive proposed by the remaining Wave Delta work. Those meanings stay
separate from controller relocation.

At this amendment's acceptance, the manual outer transport still published the
archive and sidecar to Drive and recorded the digests in an issue note. The
mandatory-local amendment below supersedes that transport. Fiat's native
commands still do not build the outer bundle or archive.

### Compatibility repair (2026-08-30)

Restore accepts the explicit controller generations that have emitted
`fiat-controller-checkpoint/v1`, rather than requiring the producer to equal
the currently installed Fiat version. An unknown or pre-checkpoint version
still refuses before marker creation.

New study and runbook receipts use portable paths relative to the run
worktree. A capsule with an older absolute source receipt is admitted only when
the recorded old origin, derived worktree and run branch agree and the source
is an exact safe descendant of that worktree. Restore verifies the same bytes
and writes the relative form into relocated state; arbitrary absolute paths,
siblings, traversal and malformed roots still refuse before mutation. This is
the sole exception to the 2026-08-29 statement that relocation changes only
the origin and worktree fields.

## Amendment: Immutable run anchors and checkpoint identity (2026-08-29)

For a new run, Fiat resolves the operator's starting branch or full commit to
one full commit before initialization writes anything. The worktree starts
from that commit and `state.base` retains it. The named branch that receives
the completed delivery remains separate in `config.git.base`.

Initialization owns a closed `fiat-run-anchor/v1` receipt. It joins the
repository and task identity, run id, run branch, integration branch,
controller identity and immutable starting commit. The initial ledger event
binds the receipt digest. A later command cannot replace the receipt or change
the integration branch it names. Verification accepts an absent receipt only
for a legacy ledger that never claimed one; when a receipt is present, every
join must still agree.

Checkpoint meaning and transport bytes have different identities. The
semantic identity is derived from the verified run anchor, accepted checkpoint
boundary and controller evidence. The native manifest digest continues to
name its exact manifest bytes and inventory. A future outer archive digest
will name exact packed bytes. Repacking a carrier can therefore change its
byte digest without changing checkpoint meaning.

A legacy state whose base is a symbolic ref cannot mint a semantic checkpoint
identity. The controller did not record which commit that ref named at
initialization, so it refuses instead of rebuilding an anchor after the fact.

Three alternatives remain rejected. Reusing the native manifest digest would
confuse exact controller-capsule bytes with checkpoint meaning. Letting the
outer archive define identity would bind the meaning to one transport and
leave inspection unable to separate repacking from a changed checkpoint. The
retired service, authority and lineage schemas would restore infrastructure
and authority claims that same-ledger local continuation does not need.

## Amendment: Mandatory local checkpoint hand-off (2026-08-30)

The outer checkpoint remains complete, but its current home is always the fixed
local checkpoint store under `<origin>/.hexaemeron/checkpoints/`. Drive and the
task issue are no longer checkpoint transports or trust anchors. The former
waiver is removed. These clauses supersede the Drive, issue-note and optional
same-machine fallback language above wherever that historical language
describes the then-current transport.

The producing agent owns the save after every successful `done push` and at an
exhausted `audit-verdict` boundary. It does not turn destination, retention or
whether to save into a user decision. It passes the verified absolute path and
digests directly to the next local agent. Failure leaves the controller at the
same accepted boundary and blocks dependent work until the archive exists and
verifies.

This is an interim transport rule, not the distributed checkpoint framework.
Adopting a remote or distributed transport later requires another accepted
change. Until then, no checkpoint operation uploads, posts, commits or pushes
the archive or its digests.

## Alternatives

- **Complete standing-checkpoint automation.** Rejected for this controller
  generation because one command would join controller mutation, archive
  parsing and key handling. The mandatory agent-side save supplies the current
  invariant without claiming that `hexctl` built the outer archive.
- **Git-only controller state.** Rejected because a branch does not carry the
  ignored controller tree, bind its receipt prefix or remove the absolute-path
  fields that prevent relocation.
- **Reuse the halted predecessor's Step 1.** Rejected because its audit did not
  cover this amendment. The successor records the decision, publishes fresh
  run artefacts and receives new implementation and audit evidence before
  controller work depends on them.

- **Fresh-ledger inoculation.** Rejected because it creates a successor run and
  reconstructs progress instead of continuing the receipted ledger.
- **Evidence-only archive.** Rejected as continuation because product evidence
  without live controller state cannot determine or receipt the next action.
- **Checkpoint service, authority signer, object-lock store and lineage DAG.**
  Retired. They add infrastructure and governance that the same-ledger
  checkpoint does not need.
- **Arbitrary mid-phase checkpoints.** Rejected because the next operator
  cannot distinguish a coherent controller boundary from a partially applied
  action.
- **Raise one cumulative audit ceiling.** Rejected because rounds 9 and beyond
  erase the exhausted-loop boundary, make the eight-round limit untrue, and
  leave no structural identity for the checkpoint or the independent loop
  that follows it.
- **Git branches alone.** Rejected because Git does not contain ignored
  controller state or its receipt ledger.

## Consequences

Continuation becomes literal and testable: exact state in, exact ledger prefix
preserved, one next directive out. It no longer requires a second Fiat run or
an interpretation layer between two ledgers.

End-of-step checkpoints remain the ordinary portable hand-off. Exhausted-loop
checkpoints preserve useful work at the point the controller must stop, while
keeping open findings, the eight-round boundary and user authority visible.
One step may therefore carry several audit loops on one ledger without
pretending they form one unbounded sequence of rounds.

The local store is the only current transport. Its fixed path makes a completed
boundary discoverable without asking the user, while native export and restore
keep the controller ledger relocatable between clean local checkouts. It makes
no claim of remote durability or distributed availability.

Checkpoint archives can be large, and every exhausted loop creates another
one. That cost is accepted in exchange for never pretending a reconstructed
ledger is the original run.

## Amendment: distributed layer reinstated (2026-09-02)

The distributed checkpoint framework this record deferred is accepted again.
[ADR-069](ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md)
is the accepted change the mandatory local hand-off amendment above asked for.
It reopens the layer above the local store rather than replacing it.

This record stays Accepted and every clause above stands. The local checkpoint
store remains the only current transport, the hand-off remains mandatory, and no
checkpoint operation uploads, posts, commits or pushes until a later delivery
accepts a transport that does. Reopening the layer authorises design records,
not behaviour, and nothing in `hexctl` changes with it.

ADR-029 through ADR-032 stay Retired. Each gains one standing successor that
carries its decision forward rebased on `fiat-v5.49.1`, so this record's
retirement of them is left as history rather than undone.
