# ADR-062: Separate live worktree reports from baselines

## Status

Accepted, 2026-08-31.

## Context

The original dead-code report accepts only a clean tracked tree. That rule
prevents a report from silently naming `HEAD` while ignoring active edits, but
it also withholds advisory feedback until those edits have been committed.
The cleanliness probe itself is small; the delay comes from the required
commit, stash or second-worktree choreography.

The checked runner already owns the repository's hardened mutable-source
capture. It binds `HEAD`, the zero-stage index and the raw bytes it places in a
disposable snapshot, then verifies that the placed source stayed intact. A
live report can reuse that boundary without weakening the committed baseline.

## Decision

Keep `report` in committed mode by default and keep its clean-tree refusal.
Add an explicit `report --worktree` mode that asks the checked runner for one
immutable source snapshot, creates a Git tree from the snapshot's tracked
index and worktree state, and runs the selected static analysers against that
tree. Untracked paths are not added to the analysed tree.

Report schema v2 replaces the ambiguous top-level commit pair with one closed
source record. It names the source kind, a recomputable source identity, the
captured `HEAD`, the analysed Git tree, the checked runner's worktree identity
when one exists, and whether the result may enter a baseline. A committed
source is baseline-eligible. A worktree snapshot is not.

Both baseline operations remain clean-only and keep the existing
`dead-code-baseline/v1` record. Coverage also remains commit-bound, so
`--worktree` refuses `--coverage` rather than combining execution evidence
from one tree with static evidence from another.

## Alternatives

Remove the cleanliness check from the existing report. Rejected because the
analysers read committed objects; accepting a dirty tree would present
unobserved edits as covered.

Make worktree reports eligible for the baseline. Rejected because the
disposable snapshot tree is not a durable repository revision and cannot be
reconstructed from a later clone.

Copy the checked runner's capture rules into the dead-code command. Rejected
because two mutable-source implementations would drift at the exact boundary
the runner already owns.

## Consequences

Contributors can inspect active tracked changes without first publishing a
commit. The report exposes both the raw capture identity and the Git tree that
the analysers consumed, so neither is presented as the other.

Snapshot construction adds local work before analysis and remains bounded by
the checked runner. It removes the workflow refusal; it is not a claim that a
live report runs faster than a committed one. Candidate counts remain
advisory, and neither report kind authorises deletion.
