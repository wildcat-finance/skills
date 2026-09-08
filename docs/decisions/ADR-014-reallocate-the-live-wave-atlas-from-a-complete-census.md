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

## Amendment: Titles are in scope, and a refresh reuses the milestones it has (2026-09-08)

The Context section lists titles among the surfaces outside the authorised
mutation. That is wrong, and the maintainer corrected it on 2026-09-08. A title
is where an issue declares its queue, so a census that may not touch titles
cannot repair the one field the queue is read from.

This amendment authorises two further mutations and withdraws one instruction.

1. **An open issue's title may be edited to make it name its queue.** The four
   forms are `{skill}-next: <summary>`, `{skill}-N: <summary>`,
   `{skill}-wish: <summary>` and `framework-N: <summary>`, and
   `hexctl issue-check` is the reader. The filed symptom carries over verbatim;
   only the queue token and the separator are the census's to write.
2. **A queue label may be corrected to the one the title's queue requires.**
   The label set is mutually exclusive: `held-job` for `{skill}-next`, `wish`
   for `{skill}-N`, `observation` for `framework-N`, and no queue label for
   `{skill}-wish`. Every other label stays outside the mutation, as before.
3. **Step 4's instruction to create fresh active milestones is withdrawn for a
   refresh.** It reads "Create fresh active milestones instead of retitling the
   prior beta milestones", which was right for the one-time move off the alpha
   and beta queues and is wrong every time after: run repeatedly it grows the
   milestone list rather than refreshing it, and Waves 19 to 22 were added that
   way on 2026-09-06 on top of Wave 0 to 18, Δ, μ and Π. A refresh assigns into
   the milestones that already exist. Creating a Wave now needs its own
   decision.

Filing prose outside the delimited status block is still never rewritten, and
`framework-N` numbers are still assigned by hand, which is the defect recorded
below rather than something this amendment fixes.

### What was done under this amendment

Read at `wildcat-finance/skills@f0ef9266` on 2026-09-08 across 269 open issues,
with the filing contract as it landed in `0ad3e363` on 2026-09-05.

- 70 titles took `: ` where an em or en dash stood between the queue token and
  the summary. No summary changed and no numbered token moved.
- 32 titles that carried no queue token were given one: 25 became
  `framework-124` through `framework-148` with the `observation` label, and 7
  became `{skill}-wish` under the skill whose code the filing names.
- 4 `framework-N` numbers that named two open issues each were reassigned to
  `framework-110` through `framework-123`, together with 10 observations that
  had no number. `framework-64`, `-74`, `-76` and `-107` now resolve to one
  issue. `framework-73` was left alone: its duplicate is closed and the four
  citations in `plugins/dokimasia/docs/` pin the open issue by URL.
- 7 queue labels were corrected, and #869's bare `elenchus-wish` title gained
  the summary its body states.
- 97 open issues that carried no Wave were assigned into 18 existing
  milestones. The repository held 26 milestones before and after; none was
  created, retitled or closed.
- 6 status blocks were written recording what `main` had already answered, on
  #882, #887, #901, #950, #1221 and #1300. The filing prose below each block
  was read back and is unchanged.

Contract-clean open issues went from 49 to 122 of 269.

### What this amendment does not settle

Two classes are left open on purpose, because each needs a decision this
document cannot make on its own.

The first is the `framework-N` body opening. The contract requires such a body
to open with exactly "Protasis decides which skill or skills this observation
upgrades. The filer is the wrong party to guess.", and 90 open bodies do not
carry that sentence at all. Rule 3 above keeps filing prose unrewritten, so the
contract currently refuses bodies it is not permitted to repair. Either the rule
is prospective from `0ad3e363` and the reader should say so, or the sentence is
insertable and this document must authorise that too.

The second is the kickoff queue. 54 open issues are titled
`kickoff/{skill}-{n}: <summary>` and every one was filed after the contract
landed, so none of them is legacy drift. They cannot become `{skill}-next`,
because that queue is one held job per skill ledger, and calling them
`{skill}-N` would file frontier work as wishes. They are a fifth queue, and they
now carry a `kickoff` label created for them on 2026-09-08. Registering that
queue is a change to the contract in `hexctl`, not to this record.

Nothing here assigns a `framework-N` number automatically, and nothing here
checks that two issues do not share one. That gap is what produced the six
collisions above.

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
