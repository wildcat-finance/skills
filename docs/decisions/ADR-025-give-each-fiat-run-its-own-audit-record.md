# ADR-025: Give each Fiat run its own audit record

## Status

Accepted, 2026-08-24. Narrows the arrangement
[ADR-012](ADR-012-run-fiat-in-a-dedicated-worktree.md) started, which gave a run
its own worktree and left its record in a file every other run wrote to.

`fiat-v5.22.1` is the generation that carries this. Steps 2 and 3 of the issue
576 runbook implement it; this record is written after them and before the
demonstration, so the present tense below describes a controller that already
behaves this way.

## Context

`done sync-run` refuses an integration receipt unless every path in the computed
integration surface carries a check recording exit 0. That surface includes the
overlap between the paths a run changed and the paths the base changed since
their merge base.

Every run appended its rounds to `audit/AUDIT.md`, from a literal in the
controller's default config. So the audit record sat on both sides of that
intersection whenever anything else merged during a run. In this repository that
is the ordinary case rather than the exception: 374 of the last thirty days'
commits on `main` touch that path, against 79 for the next one, `README.md`. It
is the most-churned path in the tree by a factor of 4.7.

Two costs followed. The file conflicted textually, in a record whose earlier
content is append-only evidence and has to survive the resolution untouched. And
the path entered `affected_paths` even when it merged cleanly, so a run that had
only appended to it owed a green check over it before it could integrate.
`tests/test_run_observation.py` reads the root log, so that is a real evidence
dependency rather than a formality.

The gate is right to ask. Exempting prose paths from revalidation would open a
hole exactly where the audit record lives, which is the last place for one. What
was wrong is that a per-run append-only record was kept at a path every other run
wrote to. Nothing about a round's evidence requires that.

Three plugins here had already reached the same conclusion on a different axis.
`plugins/probitas/audit/AUDIT.md` records why: the log sat at the repository
root, the repository was about to hold several plugins, and a top-level `audit/`
belonged to none of them. That finding moved a log by plugin. This one moves it
by run, which is the axis the sync gate intersects on.

## Decision

A run's audit record goes to a path no other run writes.

`init` derives `audit/rounds/<run branch with separators flattened>.md` from the
branch it has just cut, reusing the flattening that already names the run's
worktree directory. One run maps to one record the same way it maps to one tree.
The controller holds no literal audit path, because a literal is what a run
copies.

`config set audit.log_path` stays, because a run may legitimately keep its record
elsewhere and three plugins here do. It is no longer free. The value has to be a
relative path with no `..` component and no control character, it has to resolve
inside the target directory, and its basename has to be the one the run owns.
Move the directory if you need to. The name stays, because it is what keeps two
runs out of one file. A run whose state records no usable branch keeps the older
behaviour, because there is nothing to derive from.

The path a round records is the path it was told to write. `--log` was a free
string stored verbatim while the Warden packet named the configured file, so a
receipt could name a file the round never opened. A declared `--log` now has to
match, on both receipts, and what gets recorded is the configured path.

`audit/AUDIT.md` stays where it is, with its existing bytes untouched. It holds
every round written before this change and takes no new ones.

## Consequences

The audit record leaves the overlap set. A run that appends only to its own file
has nothing to resolve there and owes no check over it, and the historical log
stops moving, so `tests/test_run_observation.py` keeps asserting against the
history it was written for.

The record is now several files rather than one. A reader looking for what a
round found has to know which run they want. `audit/AUDIT.md` carries a pointer
saying so, and Protasis item 2 tells a study to read the run files under
`audit/rounds/` as well as the historical log.

The existing 13,090-line log is not split. 67 of its 413 sections are headed
`## Step <n>, round <r>` with no run named, so splitting it is not mechanical and
would be guesswork dressed as history. Forward-only routing is neither.

No index over `audit/rounds/` is generated. A generated listing would itself
become a tracked file every run writes, which is the arrangement this record
ends.

## Alternatives

**Exempt prose paths from `sync-run` revalidation.** The cheapest change, and it
puts the hole where the audit record lives. Rejected.

**Derive the path at the first round rather than at `init`.** `hexctl next`, the
Warden packet and `config get` would each have nothing to name before the first
round, and a branch renamed between rounds would derive two files inside one run.
Rejected.

**One file per step.** Removes nothing from the overlap set that a per-run file
does not already remove, multiplies files, and a run's rounds read better
together than apart. Rejected.
