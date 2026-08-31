# ADR-065: Bound the prose packet by what a prose pass can act on

## Status

Accepted, 2026-08-31.

## Context

Fiat's prose phase receives a packet of paths built by `scribe_files`, which
read the whole step diff and refused above `GIT_PATHS_MAX`. That constant is
500 and is shared with the commit range and the checkpoint ref set. The comment
above it said the prose diff does not grow with the base, and named it as one of
the surfaces the shared bound still fits.

The comment was wrong. The prose diff is the size of one step's change, and a
step that removes a generated tree, vendors a dependency or renames a large
directory produces thousands of paths without any of them carrying prose.

Issue #972 records the failure. `scribe_files` is reached only from
`delegation_packet`, which `next` calls, so the refusal killed the directive
rather than the phase: `next` exited non-zero and emitted nothing, and the run
could neither execute the prose phase nor receipt it. Issue #949's step 3
removes the 995 generated files under
`.agents/skills/promise-machine/runtime/` for a branch diff of 1,006 paths, and
stopped there. A runbook amendment may not add or renumber a step, so that run
could not split the deletion to get under the bound.

Integration revalidation already recognised this shape. `INTEGRATION_PATHS_MAX`
is 4,096 because the composition delta grows with the base. The prose packet
grows with the work, and had neither its own ceiling nor an accurate comment.

## Decision

The prose packet is selected by what a prose pass can act on, and it carries a
ceiling of its own.

`scribe_files` excludes deleted paths on the `git` invocation's own argv rather
than filtering them afterwards, so every existing UTF-8, absolute, dot and
`scoped_path` refusal still runs over the set it returns. What remains is
bounded by `PROSE_PATHS_MAX`, set at 4,096 and separate from
`INTEGRATION_PATHS_MAX` because the two surfaces answer to different work and
may diverge. The refusal above that ceiling names the prose packet and states
that deletions are already excluded, so a reader knows the count is authored
surface rather than a removed tree.

`GIT_PATHS_MAX` keeps the value 500 and its two remaining call sites, the
commit range and the checkpoint ref set, neither of which grows with the work.
The comment above the constants no longer claims otherwise.

A removed path carries no prose to rewrite. Excluding it loses nothing a prose
pass could have done, and it is what lets a payload-removal step reach the
phase at all: the count that stopped it was a count of files with no prose in
them. Everything added, modified, renamed or copied is retained, and a rename
arrives under its new name.

## Alternatives

- **Exclude registered generator prefixes.** Join the diff against
  `GENERATOR_AGGREGATE_REGISTRY` and drop paths under a registered prefix.
  Rejected on the dependency alone: it couples the prose packet to a registry
  holding one entry that issue #971 is queued to remove, and that entry's
  status is already contested. A selection rule should not acquire a dependency
  on a table that is being retired.
- **Select by prose-bearing extension.** Keep only the paths a prose pass
  reads. It produces the smallest packet and is the only option that can
  silently drop real prose: a changed description string or a module docstring
  sits in a file the filter discards, and the pass then reports success having
  read nothing. Issue #972 names silent truncation as the thing to avoid.
  Rejected.
- **A separate named ceiling alone.** Give the call its own constant and change
  nothing else, as #774 did for integration. It moves the cliff from 500 to a
  larger number without changing the shape, and leaves the comment still wrong
  about why. Taken as half the decision rather than the whole of it.

## Consequences

A step that removes a generated tree reaches its prose phase. Issue #949's step
3 returns 10 authored paths where it previously refused at 1,006, and the 995
deletions it drops are the generated payload.

The trade is stated rather than removed. A step that *adds* a large generated
tree is handled by the ceiling and not by the filter, so the reported shape is
fixed and its mirror image is not. At 4,096 that is headroom rather than a
guarantee, and the number is inherited from `INTEGRATION_PATHS_MAX` rather than
measured against an authored diff of that size. No prose pass has been run over
one.

The two ceilings are deliberately separate constants that happen to be equal
today. A later reader who re-couples them because the numbers match would
reintroduce the fault this record exists to explain.
