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

When Drive is available, one checkpoint archive and its outer SHA-256 sidecar
go in the HexaemeronCheckpoints parent folder. The run's issue receives the
archive digest, state and ledger digests, ref boundary, expected directive and
restore rule. The issue note is the trust anchor; the sidecars support local
verification.

When Drive is unavailable and continuation will happen on the same machine,
copy the literal `.hexaemeron` directory outside the live worktree, omit the
transient lock, write the sorted recursive SHA-256 sidecar beside it, and keep
both untouched. Preserve the exact Git worktree and its object store. Put that
copy back into the next agent's room before any controller action. This is the
authorised local fallback, not an evidence-only substitute and not a new run.

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

The manual outer transport remains in force. A contributor still prepares and
verifies the Git bundle, commit-signature proof, checkpoint archive and outer
sidecar, publishes the archive and sidecar to Drive, and records the digests,
ref boundary and restore rule in the issue note. Fiat's native commands neither
build nor publish those objects. This retained manual procedure is the accepted
trade for closing the path-relocation gap without combining controller state,
credentials, archive parsing and network writes in one operation.

## Alternatives

- **Complete standing-checkpoint automation.** Rejected because one controller
  command would join credentials, archive parsing, GitHub and Drive writes,
  key handling and work reserved for the unresolved outer-archive and identity
  designs.
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

The same-machine fallback is intentionally path-bound. A Drive package can
carry the bytes and Git objects to another machine, but current controller
state still records local worktree paths; no claim of native relocation is made
until the controller has a checked export-and-restore transition for it.

Checkpoint archives can be large, and every exhausted loop creates another
one. That cost is accepted in exchange for never pretending a reconstructed
ledger is the original run.
