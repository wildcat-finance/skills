# ADR-057: Require explicit sync resolution acknowledgements

## Status

Accepted, 2026-08-30. This record fixes the controller rule selected for issue
[#891](https://github.com/wildcat-finance/skills/issues/891).

## Context

A valid two-parent Git merge can discard concurrent work without carrying a
conflict. Selecting an entire parent tree for a shared registry produces a
clean commit with the expected `[product, base]` parents. Rebuilding an older
composition against a newer base can also drop a resolution that existed only
in the older merge.

Fiat already proves the sync's parents, signatures, remote tips and green
path-scoped checks. None of those records whether its tree equals one complete
parent at a divergent shared path, or whether a rebuilt sync revisited every
path changed by both the old composition and the later base advance.

## Decision

Every new `done sync-run` receipt carries
`fiat-sync-resolution-guard/v1`. The controller derives two sorted path sets
from native Git objects before it writes state:

1. `side_selected_paths` contains paths changed by both product and base from
   their common ancestor where the parent entries differ and the sync entry is
   exactly either complete parent entry.
2. `superseded_intersection_paths` contains the intersection of the old
   `product..sync` composition delta and the old-base to new-base advance when
   an active sync is replaced.

The required acknowledgement set is the exact sorted union of those arrays.
The operator repeats `--acknowledge-sync-path` once for each path in that order.
Missing, extra, duplicate, unsorted or unsafe values refuse before mutation.
The receipt retains the risk arrays and acknowledgement array, status prints
their counts, and integration recomputes them from the stored commits.

Tree identity means Git mode, object type and object id, or absence. Reads use
the controller's native relation boundary: replacement objects and inherited
Git configuration are disabled; fixed argv, literal pathspecs, path and output
caps, and the Git deadline remain in force.

An acknowledgement records inspection. It does not prove that the chosen
content is correct and does not replace integration revalidation. A legacy
active sync without this record must be superseded with a fresh signed and
revalidated sync before integration.

## Alternatives

**Ban merge porcelain commands that select a side.** Rejected. Fiat cannot
observe how a pushed tree was built, and the same tree can be created without
those commands.

**Reject every divergent overlap.** Rejected. It has no bounded route for a
legitimate semantic resolution.

**Teach Fiat to merge known registry formats.** Rejected. It would make the
delivery controller a content merger and leave every unregistered shared file
outside the rule.

## Consequences

Whole-side and rebuild-loss candidates become visible and fail closed until an
operator names each path. Legitimate merged content with a third tree entry
does not need a whole-side acknowledgement. Supersession remains stricter: the
old-composition/base-advance intersection always requires inspection because
tree equality cannot show whether an earlier manual resolution was preserved.

The controller performs bounded extra Git reads over an integration surface
already capped at 4,096 paths. Receipts grow only by those bounded path arrays.
Historical completed receipts remain historical evidence; this decision does
not rewrite them or claim that they carried a guard they predate.
