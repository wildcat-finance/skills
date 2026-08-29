# ADR-049: Bound integration revalidation apart from commit ranges and prose diffs

## Status

Accepted, 2026-08-29. This record fixes the design selected for issue
[#774](https://github.com/wildcat-finance/skills/issues/774). It exists because
the same change was made once before, reverted for an unrelated reason, and
then declined a second time on scope, so the cause needs to outlive the pull
request that carries it.

## Context

One constant, `GIT_PATHS_MAX = 500`, served five call sites in `hexctl.py`. Two
of them read an integration surface. Three do not.

The two that do are the integration path delta reader, `git_diff_paths`, and
the revalidation artefact's path arrays, `_manifest_paths`. Both are reached
only from `integration_revalidation_record`, `_integration_checks_v2` and
`_integration_revalidation_record_v2`, and nothing else in the controller
reaches either.

The three that do not are `exact_commit_range`, which bounds a range measured
in commits rather than paths, `scribe_files`, the general prose diff reader,
and `_checkpoint_ref_names`, which bounds a checkpoint's Git ref set. The
issue named four call sites; there are five, and the checkpoint ref set is the
one it missed.

Integration surfaces grow and the other three do not. `done sync-run` pins the
sync commit's first parent to the final recorded step merge, so `product_head`
never advances past it and the composition delta spans the base's entire
advance since that merge. A completed sync does not reset the baseline.
Measured on issue [#556](https://github.com/wildcat-finance/skills/issues/556):
693 outside paths at one base, 702 about four and a half hours later. Waiting
does not shrink that and rebuilding against a newer base enlarges it. That run
is finished, signed and audited, and it cannot receipt.

## Decision

Give integration revalidation its own ceiling, `INTEGRATION_PATHS_MAX = 4096`,
read at those two sites and nowhere else. `GIT_PATHS_MAX` stays at 500 and
keeps guarding the other three.

The byte ceilings do not move and remain the real protection.
`SOURCE_BYTES_MAX` is 2 MiB and bounds the artefact before it is parsed;
`GIT_OUTPUT_MAX` is 2 MiB and bounds what the Git reader returns; `GIT_TIMEOUT`
is 30 seconds. Issue #556's prepared artefact is 82,849 bytes for 688 paths, so
4,096 paths stay an order of magnitude inside the byte bound. The path grammar,
the 4,096-byte per-path length limit and the `allowed` set that confines every
declared path to the computed delta are all unchanged. Only the count moved.

`fiat-integration-revalidation/v2` is untouched. Its aggregate rules, its
1,024-file and 32 MiB ceilings and its source registry are exactly as
[ADR-044](ADR-044-bind-sync-run-generator-aggregates.md) fixed them.

## Alternatives

**Raise `GIT_PATHS_MAX` to 4,096.** One constant instead of two. Rejected: it
loosens a commit-range bound measured in commits, a general prose diff reader
and a checkpoint ref set, none of which this change has evidence about and none
of which grows with the base.

**Make the outside-path count aggregate-aware, so paths absorbed by a
registered aggregate stop counting against the individual limit.** Rejected: a
larger change to the version-2 contract that does not help the case that
motivates the work. Issue #556's residual 702 paths are hand-authored source
across twelve plugins plus docs, audit records and tests. No generator owns
them, so no aggregate forms over them however the counting is arranged.

## Prior art, and why it is not a rejection

[#679](https://github.com/wildcat-finance/skills/pull/679) made this change and
it was green. [#680](https://github.com/wildcat-finance/skills/pull/680)
reverted it wholesale to #679's first parent because the continuation it was
unblocking had been cancelled. That revert records no defect in the change and
states no objection to its shape.
[#710](https://github.com/wildcat-finance/skills/issues/710) then declined to
raise the bound from inside a halted run, calling it a maintainer decision.

Anyone who reads #680 and #710 without #679 gets the wrong impression: that
this was considered and rejected. It was neither. This record is that maintainer
decision being taken deliberately.

## Consequences

Issue #710's acceptance 1 is superseded. It asserted that version 1 refuses the
1,095-path incident on its count, which was true of the entry controller and is
not true now. Its case records that refusal as history, asserts the count no
longer stops the artefact, and leaves the aggregate acceptances alone. Version
2 keeps its value for surfaces above 4,096 paths and for the aggregate
accounting itself, and its justification narrows rather than disappearing.

Three checked-in digests over `hexctl.py` move with any controller change and
moved with this one: the runtime binding digest in the Promise Machine coverage
manifest, the issue 429 recovery pin, and the issue 622 inoculation record with
its verifier. They are a standing cost of editing the controller, not a
consequence of this decision.

A surface above 4,096 integration paths still refuses, before any state or
ledger byte changes, and an artefact over `SOURCE_BYTES_MAX` still refuses
whatever its path count. Ten cases pin both halves. Five are guards and fail
with the bound reverted. Five hold the three unchanged sites, a small version-1
surface and the byte ceiling, and pass in both directions because their purpose
is that those surfaces did not move.
