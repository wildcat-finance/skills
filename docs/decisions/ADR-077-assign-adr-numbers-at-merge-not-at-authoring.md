# ADR-077: Assign ADR numbers at merge, not at authoring time

## Status

Proposed, 2026-09-02.

## Context

Decision records are currently named and headed with a number while a branch is
being authored. A concurrent merge can take that number before the branch
reaches the default branch. Different filenames then hide the collision from
Git until a repository-wide check runs. The issue that motivates this record
preserves two drafts and the earlier collisions as evidence of that race.

The repository already has a stable Fiat integration boundary and a
Hypomnema record-shape check, but neither one owns a number at the moment the
final tree is composed. A branch-local maximum is therefore an observation,
not an exclusion rule.

## Decision

New records are authored as `docs/decisions/drafts/<slug>.md` with the stable
identity `adr/<slug>` and a numberless decision heading. Immediately before
the final integration merge, a bounded allocator reads the exact protected
base and signed product objects, chooses the greatest number present on that
base plus one, and changes only the draft path and first heading. The report
records the exact objects and ordered mapping. A base-owned status gate refuses
a candidate whose assignment base is stale or whose composition lacks the
active assignment evidence.

Existing numbered records and their numeric references are unchanged. This
record receives its final number only in that merge-time composition.

## Alternatives

- Reserve a number in a shared authoring ledger. Rejected because abandoned
  reservations create another authority and still leave a merge-time gap.
- Re-read the default branch immediately before merging. Rejected because two
  candidates can read the same tip before either merge.
- Use an issue or pull-request number. Rejected because those identifiers
  belong to separate queues and do not express decision order.
- Remove numbers permanently. Rejected because the repository's accepted
  records and reader-facing convention already use numbered identities.

## Consequences

Draft references stay stable while work is reviewed, and a stale candidate has
an explicit recovery: recompute against the new exact base. Numbers may have
gaps because allocation never fills a hole. The allocator and hosted gate add
bounded checks and reports, but no service, credential, or live ruleset change.
Until a separately authorised ruleset activation makes the status required,
the repository proves the mechanism locally and does not claim production
race-freedom.
