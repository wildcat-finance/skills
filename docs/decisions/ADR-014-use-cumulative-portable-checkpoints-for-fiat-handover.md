# ADR-014: Use cumulative portable checkpoints for Fiat handover

## Status

Proposed, 2026-08-22. It remains Proposed until issue #439 lands and
`archive-core` proves the required refusal cases.

## Context

Wildcat Labs originated the checkpointing design so a contributor can stop a
Fiat run and another contributor can resume from the same evidence. Fiat keeps
its controller state and hash-chained ledger in the ignored `.hexaemeron/`
directory. A Git branch preserves committed work but does not preserve that
state, the index, unfinished worktree changes, untracked contribution files,
or the current directive.

A checkpoint may be taken partway through a step, after commits or pushes, or
after newer `main` work has been integrated. The mutable name `main` therefore
cannot establish the starting point later. Portability has to preserve three
separate facts: the authored Git history, the unfinished filesystem state, and
the verified controller evidence.

Issue #439 defines the dedicated-worktree boundary that safe restoration needs.
It is not part of the accepted base yet. Portable import and controller
integration must wait for it.

## Decision

Each portable checkpoint is a cumulative package measured from the full commit
SHA used to create the run's first worktree. That initial base never changes
for the run, including after a commit, push, patch, or integration from `main`.

The package is independently restorable from that base. It binds authored
commits, a cumulative patch, separate index and worktree patches, and verified
`.hexaemeron` state by digest. A missing earlier checkpoint must not prevent a
later accepted checkpoint from being checked and restored.

The accepted parent chain determines progress. The displayed stage is the
one-based depth of that chain, not a number supplied by the uploader. A
furthest-checkpoint request returns the unique verified leaf. If two accepted
children leave the lineage with competing leaves, the request returns `409`
and exposes the conflict; it never chooses by upload or creation time.

No portable importer may restore into the caller's checkout. Import and
controller integration remain blocked until issue #439 provides the accepted
isolated-worktree semantics.

## Alternatives

- **Store an incremental patch chain.** This uses less storage, but every
  restore has to process all earlier untrusted objects. One missing object
  strands every descendant and prevents independent retention.
- **Use Git branches and pull requests alone.** They already transfer authored
  commits, but they omit ignored controller state, index state, unfinished
  files, and the exact current directive.
- **Archive the complete worktree.** This is simple to capture, but it
  duplicates Git objects, includes ignored build output, increases secret
  exposure, and weakens the recorded relation to the initial base.
- **Write checkpoints as Git commits on a service branch.** This would make
  storage and inspection easy, but synthetic commits change the meaning of
  unfinished index and worktree state and confuse authorship with upload
  identity.
- **Choose a fork by timestamp.** This always returns an answer, but it hides
  concurrent valid work and lets arrival order stand in for verified progress.

## Consequences

Cumulative archives repeat bytes that an incremental chain could share. In
return, each accepted object can be checked and restored without trusting the
availability or validity of every earlier archive. Git authorship remains
separate from the identity that uploads the package.

Lineage conflicts stay visible and stop automatic furthest-checkpoint
selection until they are resolved explicitly. A caller cannot claim progress
by choosing a large stage number, and a later movement of `main` cannot rewrite
the run's starting point.

This record chooses the format and ordering rules only. It does not add a
checkpoint command, importer, remote store, public download, deployed API, or
Atlas integration. Issue #439 remains a prerequisite, and the design remains
Proposed.
