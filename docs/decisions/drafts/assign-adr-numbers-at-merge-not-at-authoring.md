# Decision: Assign ADR numbers at merge, not at authoring time

## Status

Accepted, 2026-08-30. The stable identity for this unnumbered record is
`adr/assign-adr-numbers-at-merge-not-at-authoring` until integration assigns
its number.

## Context

The repository currently chooses a decision-record number while a delivery is
being authored. Two branches can therefore choose the same next number from
the same base. Their filenames can still differ, so Git need not report a
path conflict when both records are composed. Re-reading the default branch
before integration narrows that race but does not remove it, and renumbering a
late branch leaves frozen studies and runbooks naming the old number.

Existing numbered records and their references are durable history. New
records need an identity that survives assignment, while their final numbers
must still follow the repository's sequence. The repository can implement and
test that mechanism before the live branch rules enforce it, but it cannot
claim production exclusion while the required-status ruleset remains in
evaluation mode.

## Decision

Authors place new records under `docs/decisions/drafts/` with a lowercase
ASCII slug and a first heading beginning `# Decision:`. Prose refers to the
record as `adr/<slug>` before and after assignment.

The final signed Fiat composition assigns numbers from one exact integration
base. It takes the greatest number already present in that base, ignores lower
gaps, orders multiple draft slugs by ASCII bytes, and assigns the following
contiguous numbers. The transform changes only each path and exact first
heading. It preserves every other byte and the file mode, and it records the
base, product, result tree, mapping, and input and output blobs in one
canonical report. The signed composition and Fiat receipt bind the same base
and ordered mapping. If the base advances, the composition is stale and the
mapping must be rebuilt from the unchanged product tip.

A base-owned status check validates the exact pull-request head without
executing candidate code. Race-free admission additionally depends on an
active required-status ruleset with strict up-to-date checks and no bypass.
Activating that external gate and proving it with a canary are separate
operations. Existing numbered records and numeric references are unchanged.

## Alternatives

**Reserve a number when authoring starts.** Rejected because it assigns the
number too early, needs policy for abandoned reservations, and moves the race
to a separate mutable ledger.

**Use the issue or pull-request number.** Rejected because that creates a
sparse second namespace tied to an unrelated queue rather than the order in
which decisions enter the repository.

**Re-read the default branch immediately before merge.** Rejected because two
candidates can read the same base before either enters it. The shorter window
is still a window.

**Stop numbering new records.** Rejected because stable slugs alone remove the
collision by discarding the repository's established numbered convention,
which this decision is meant to preserve.

## Consequences

Authors and frozen run artefacts use one stable reference and do not change
when integration assigns the number. Number allocation becomes reproducible
from exact Git objects, and a base advance makes stale evidence visibly
invalid. Existing records are not renamed, and unused lower numbers stay
unused.

The repository gains a bounded allocator, assignment report, Fiat receipt
extension, and base-owned status context. Those parts make the mechanism
larger than the current branch-local check, but they expose the base and
mapping that decide the result. The checked-in implementation can prove local
stale-base refusal. It does not prove production race freedom until a later,
separately authorised operation activates and verifies the external gate.
