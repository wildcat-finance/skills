# ADR-014: Reallocate the live Wave Atlas from a complete census

## Status

Accepted, 2026-08-23.

## Context

The Wave Atlas is the contributor-facing view of the Wildcat Skills issue
queue. Its active allocation had been built from a complete 79-issue census,
then changed incrementally as issues closed and new issues were filed. The
result still assigned every open issue, but the milestone descriptions no
longer described every member and the deployed Atlas served an older compiled
snapshot.

The reallocation had to compare every live open issue with every other one.
Shipped gates that returned false-clean or overstated their evidence had to
outrank new capability work. Active delivery blockers and work already in
progress also had to remain visible. Numeric priority alone was insufficient:
hard dependencies and coherent implementation bundles constrain which work can
usefully precede other work.

Four framework-introspection issues, #434 through #437, were explicitly moved
to a separate Handover milestone. Closed issues had to retain their historical
assignments, while the superseded alpha and beta milestones were closed after
the active queue moved. Issue bodies, titles, labels, assignees, comments, and
project membership were outside the authorised mutation.

## Decision

Rebuild the active Wave Atlas from the complete live open-issue universe, using
GitHub milestones as the only Wave assignment.

Apply these rules:

1. Query all live open issues, all milestones, open pull requests, active
   branches, the repository head, and each governed skill frontier before
   scoring.
2. Score relative priority on impact out of 40, urgency out of 25, readiness
   out of 20, and unblocking value out of 15. Apply hard dependencies,
   in-progress work, and coherent implementation bundles outside that score.
3. Clear the milestone field from every open issue before assigning the new
   queue. Assign each open issue exactly once to Wave 0 through Wave 11, except
   #434 through #437, which belong to Handover by explicit governance
   decision.
4. Create fresh active milestones instead of retitling the prior beta
   milestones. Close the superseded alpha and beta milestones after successful
   reassignment, leaving their completed issues attached.
5. Preserve a rollback snapshot before mutation. Use sequential REST updates
   with bounded retries, then verify the live issue universe, exact
   issue-to-milestone mapping, milestone counts, omissions, and duplicates.
6. Rebuild the deployed Atlas snapshot from the verified post-mutation GitHub
   state. Label it as a verified snapshot rather than a live index, preserve
   recorded dependency edges, test the public job pool, and verify the
   production route after deployment.

Milestone descriptions hold the score and concise ordering reason for every
current member. They are the durable ranking record for this allocation.

## Amendment: Authorise a delimited status block in issue bodies (2026-08-31)

The alternatives below reject writing Wave metadata into issue bodies, because
that creates a second source of truth and changes issue content. That reasoning
holds for Wave assignment and is unchanged here. The milestone field stays the
only Wave assignment, and nothing may write a Wave into a body.

It does not extend to an issue's current requirement. A Wave has a canonical
GitHub field, so writing it into prose duplicates a value that already exists.
Requirement drift has no such field. When an open issue is narrowed by work that
landed, subsumed by a later issue, or invalidated by a change to `main`, the only
surfaces available are the body and the comment thread.

The comment thread is the weaker of the two, and the difference is measured.
Issue #838 read 213 issues and 583 closed pull requests and found 436
carried-forward items across pull-request bodies and issue closing comments, of
which 344 name no issue or pull request and 245 have no register anywhere. A
correction that arrives as the fourteenth comment is not read by a census that
reads bodies.

This amendment authorises one further mutation, bounded as follows.

1. An open issue's body may be edited to record current status, supersession, or
   a changed requirement. The edit is confined to a single block at the top of
   the body, delimited by `<!-- status:start -->` and `<!-- status:end -->`.
2. Wave assignment remains milestone-only. No Wave, score, or ordering value may
   be written into a body.
3. Filing prose outside the delimited block is not rewritten. Where a filing is
   wrong rather than stale, the block says so and the original text stays, which
   keeps the append-only amendment discipline that governs documents.
4. The Atlas dependency extractor must ignore the delimited block. It parses
   bodies for dependency declarations, and issue #497 records it reading a
   `depends on` line as a declaration about the issue that contained it. A status
   block naming other issues would otherwise change eligibility.
5. Titles, labels, assignees, comments, and project membership stay outside the
   authorised mutation, as the Context section states.

This amendment does not address issue #894, which records that this document
misstates what happened to the superseded alpha, beta, and Handover milestones.
That correction needs its own amendment and a decision about whether closed
issues should carry a Wave at all.

## Alternatives

- **Patch only the issues added since the previous census.** This would be
  faster, but it would retain priority assumptions made before the current
  controller fixes, live branches, false-clean findings, and contributor
  handover work existed.
- **Retitle and reuse the beta milestones.** This would reduce milestone
  count, but completed issues attached to those milestones would be silently
  reclassified under the new allocation.
- **Order only by the numeric score.** This gives a simple ranking, but it can
  place consumers before their prerequisites and split changes that should be
  made and reviewed together.
- **Write Wave metadata into issue bodies.** This creates a second source of
  truth and changes issue content. GitHub milestone fields already provide the
  canonical assignment and counts.
- **Use one parallel bulk mutation.** This is faster when the API is healthy,
  but previous and current runs both observed transport failures. Sequential,
  state-checked writes make a partial result recoverable.
- **Continue calling the deployed Atlas live.** The site packages issue data
  into a build artefact. A no-store response header does not make that source
  live, so the label would overstate the evidence.

## Consequences

The active queue has one complete point-in-time allocation with no open issue
missing or duplicated. Current Waves and Handover are separate from closed
historical alpha and beta allocations, so completed work keeps its original
context without presenting those milestones as active queues.

The earliest Waves favour delivery continuity and truthful existing gates over
net-new capability. Later Waves follow dependency chains through fixtures,
ingestion, release representation, statements, accessible interaction, and
maintenance. Handover is an explicit exception to the numeric sequence.

The allocation is not self-updating. A new or closed issue can make the
snapshot and its relative scores stale. A future refresh must repeat the full
census and post-mutation verification; editing only the compiled Atlas file is
not sufficient evidence that GitHub and the site agree.

The public job endpoint remains a draw from dependency-clear issues, not a
claim that every offered issue has equal importance or that Wave order is a
hard dependency.
