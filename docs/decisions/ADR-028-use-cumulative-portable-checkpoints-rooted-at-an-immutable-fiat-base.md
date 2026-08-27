# ADR-028: Continue Fiat only from resumable checkpoints

## Status

Accepted, 2026-08-27, at the Creator's direction. This decision replaces the
portable-checkpoint service proposal previously recorded here and retires
ADR-029 through ADR-032.

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

An exhausted audit remains halted until the user authorises more rounds. To
continue the same audit, first checkpoint the exhausted boundary, then while
halted raise `audit.max_rounds` to a higher total, receipt the resume note, and
run `verify`, `status`, and `next`. For example, an eight-round run continues
with a total of sixteen; another exhausted block can move to twenty-four.
`next` must return the next audit round. Raising the ceiling does not accept or
close any finding, and the ordinary ceiling is restored to eight after that
step's audit closes so later steps do not silently inherit the exception.

Historical archives, issue comments and filenames that use `carryover` or
`inoculation` remain evidence of what happened. They do not authorise that
procedure for a current continuation.

## Alternatives

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
- **Git branches alone.** Rejected because Git does not contain ignored
  controller state or its receipt ledger.

## Consequences

Continuation becomes literal and testable: exact state in, exact ledger prefix
preserved, one next directive out. It no longer requires a second Fiat run or
an interpretation layer between two ledgers.

End-of-step checkpoints remain the ordinary portable hand-off. Exhausted-audit
checkpoints preserve useful work at the point the controller must stop, while
keeping open findings and user authority visible.

The same-machine fallback is intentionally path-bound. A Drive package can
carry the bytes and Git objects to another machine, but current controller
state still records local worktree paths; no claim of native relocation is made
until the controller has a checked export-and-restore transition for it.

Checkpoint archives can be large, and every exhausted block creates another
one. That cost is accepted in exchange for never pretending a reconstructed
ledger is the original run.
