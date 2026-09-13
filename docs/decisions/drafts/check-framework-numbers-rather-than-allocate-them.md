# Decision: Check that a `framework-N` is free, and keep assigning it by hand

## Status

Accepted, 2026-09-12. The record takes its number at the integration
composition, where the merge composer assigns one from the base branch.

## Context

ADR-009 gave the four issue queues their title prefixes and left two questions
open, recording them in #370 rather than guessing: who assigns `N` in
`framework-N` when two runs file at once, and whether a skill spin-off needs a
label of its own. #370 closed without answering either.

Nothing allocated the number and nothing refused a second claim on one, so
collisions accumulated. #1476 recorded six numbers naming two issues each at
`f0ef9266`, and the 2026-09-08 Wave Atlas census reassigned the four
open-against-open pairs to `framework-110` and above. Four days later, on
2026-09-12, the repository held four more: `framework-65` (#962, #972, both
closed), `framework-108` (#1437, #1531), `framework-109` (#1467, #1534) and
`framework-110` (#895, #1538). Three of those were open against open, and one
sat on a number the census had just issued to repair an earlier collision.
Repair without a gate is a number that comes back.

The collision matters because of how the number is used. `framework-N` is the
shorthand this repository writes in prose, and it is far from the issue number:
`framework-71` is #1021. A reader resolving the shorthand by title search
against a duplicated number gets two rows and no way to tell which was meant,
and that has already sent work to the wrong topic.

## Decision

`issue-check` refuses a `framework-N` whose number another issue already holds.
It asks one bounded `search/issues` read with `in:title`, re-matches every row
against the title rule, and compares the parsed number exactly, so a
`framework-11` row does not make `framework-110` a duplicate. Closed issues
count: closing an issue does not free a number the tree still cites, and #1036
is cited by URL for precisely that reason. An issue that has already been filed
holds its own number and is not its own duplicate.

The check runs only after the title has passed its shape rule, because an
ill-formed title carries no number to be unique about, and only in
`wildcat-finance/skills`, whose prose uses the shorthand. A search that cannot
answer refuses in the transport's own shape, so an unreachable read never
passes as a free number.

Nothing allocates `N`. A filer picks the lowest free number and the check
settles whether they were right.

## Alternatives

**Allocate the number.** A register in the tree, or a reservation step, would
stop two filers picking one number rather than catching them afterwards. It is
the harder half, it needs somewhere durable to keep the register, and the same
class of defect for `ADR-` numbers is open in #1332. Catching a collision
before the issue is filed removes the ambiguity the prose suffers from; the
race that produces it can be addressed once there is a register worth writing.

**Retire the number and cite the issue number.** GitHub already guarantees
issue numbers unique, so `framework` would become a bare queue marker and the
whole class of defect would go. It trades the shorthand people actually use in
conversation and in prose, and it would strand every existing citation. That is
a governance call about how the repository refers to itself, not a call this
change is entitled to make, so it stays open.

**Check at census time instead.** The 2026-09-08 census found and repaired four
collisions, and four more existed four days later. A periodic sweep repairs;
only a gate prevents.

## Consequences

A `framework-N` candidate cannot be filed onto a number already in use, and a
filed issue that collides is reported by `issue-check --issue`. The four
collisions live on 2026-09-12 are not repaired by this change: renumbering a
filed issue moves the shorthand its citations use, so each one is a separate
decision for whoever owns those issues.

`issue-check` now makes a network read for a `framework-N` title where the
`--body` path previously made none. The command already required `gh` for its
`--issue` path, and the prose phase that runs it before filing has a network,
so the cost is one search request rather than a new dependency.

The gate is only as good as the search index. A candidate checked against an
issue filed seconds earlier can pass, because the read establishes what search
reported and not what exists. Two filers racing inside the indexing window
still collide, which is the allocation problem this decision leaves open.
