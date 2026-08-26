# ADR-034: Recover the signed Fiat product through a compatibility merge

## Status

Accepted, 2026-08-25.

## Context

Pull request #552 contains the completed issue 429 product, including 52 signed
commits. Its controller ledger no longer exists, so those commits cannot resume
their old run. Meanwhile, `main` has moved to Hexaemeron 1.6.0 and Fiat 5.24.1.
That version gives each run its own audit file, while #552 assumed every audit
round lived in `audit/AUDIT.md` and every source used the same synopsis name.

Replaying the old commits would replace their object identities. Taking either
side of the merge wholesale would lose either the product or the current
controller. Appending the old audit bytes to the current root log would also
rewrite the evidence boundary that the current base already published.

## Decision

Recover #552 with one signed merge whose first parent is its immutable head and
whose second parent is the pinned current base. Keep the current root audit log
unchanged. Store the exact 574-line product audit suffix in its own per-run
source. Read its historical topic-bearing records as
`fiat-audit-round/v1`, and write new path-bound records as
`fiat-audit-round/v2`.

Legacy `AUDIT.md` sources keep `AUDIT_SYNOPSIS.md`. A direct
`audit/rounds/<run>.md` source maps to `<run>.synopsis.md`. Discovery excludes
those outputs and refuses any source set that maps twice to one destination.
The composition manifest records how every overlapping path retained the
current and product behaviour.

## Alternatives

- Replay or reimplement #552 on the current base. This would make a simple
  linear diff, but the 52 reviewed and signed commit objects would no longer be
  the delivered ancestry.
- Merge and choose one side for every conflict. Keeping the product side would
  roll back current controller gates. Keeping the base side would retain the
  commit graph while silently dropping the feature those commits built.
- Leave #552 as an archival branch and implement issue 429 again. This would
  preserve an archive but duplicate the work and review without recovering the
  product into the release.

## Consequences

The history shows three things separately: the old product, the pinned base,
and the compatibility decision. Reviewers must inspect one deliberately large
merge, but they can verify its exact parents and the 16-path composition
manifest. Audit tooling carries two explicit record grammars and two output
naming rules. The root audit bytes and all inherited commit objects remain
unchanged, and future base movement uses Fiat's existing product-first sync
gate rather than a rebase or force update.
