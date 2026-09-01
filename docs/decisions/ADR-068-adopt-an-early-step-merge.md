# ADR-068: Adopt an early step merge rather than refuse it

## Status

Accepted, 2026-09-01.

## Context

A Fiat run merges its step stack in the integrate phase, bottom up. Nothing is
supposed to merge while the steps run. When somebody merges a step's pull
request anyway, minutes after it opens, the run has no way forward.

Issue 1021 records it happening. During the 972 run both stacked pull requests
were merged into their bases before integrate: 1014 into the run branch as
`ee1634c8`, then 1017 into step 1's branch as `d1c83b99`. Step 2's push receipt
was attempted three minutes later and refused. Recovery took a maintainer
force-pushing step 1's branch back to `749c30f6`, the head its own push receipt
had already recorded, so step 2 regained a diff and could open a replacement
pull request. Rewriting a published ref to unstick a run is not a recovery an
agent should need a human for.

One thing about the mechanism is not what the issue's own cause section says,
and one thing the issue says is right in a way worth stating exactly.

`done push` is merge-blind for a step, as the issue claims. `--merge-commit` is
registered on the shared `done` parser and does reach `done_push`, but for a
stacked step `done_push` refuses it before it ever calls `inspect_pull_request`,
with "a step pull request does not merge during the run". Every run since 3.4 is
stacked, so the merge-aware branch inside `inspect_pull_request` cannot be
entered from a step push and the early-merge refusal is the only outcome. That
matters for the decision below: adoption cannot be gated on an operator flag,
because the flag a step push would need is the one it refuses.

The head evidence the issue argues survives an early merge is already enforced,
one screen earlier, before the merged state is consulted at all. A pull request
whose head is not the receipted head refuses first, merged or not.

So a step has no reversal path at all, and no record it could leave. A push
receipt whose `merge_commit` happened to be populated would not be a statement
that this step merged early, only a value a reader may infer one from, and on the
stacked path it cannot be populated in the first place.

The dead end also has a second half, one call frame further on. `done merge-step`
takes its expected base from the integrate directive, whose `into` is always the
run branch. A step pull request that merged early landed in its stacked base,
which for step N is step N-1's branch. The bases disagree,
`inspect_pull_request` refuses, and a merged pull request's base cannot be
retargeted. Relaxing the push alone would therefore move the refusal rather than
remove it, which is why the decision below covers both halves.

## Decision

An early merge is adopted, explicitly and once, at the transition that first
observes it.

**`done push` owns the adoption.** It is the first transition to look at the
pull request after the merge, and it already holds the recorded head and the
recorded base the merge has to be reachable from. Adopting there means one
observation, one receipt and no window in which the run knows about a merge it
has not recorded. The two hard gates are the price of admission: the pull
request head must still equal the receipted head, and the merge commit must be
reachable from the recorded base. A bounded native `merge-base --is-ancestor`
answers the second, and an unanswered query refuses as unknown rather than
passing, following the form issue 923 established for a moved step branch.

**The receipt says so in its own words.** The push receipt carries an explicit
`early_merge` block naming the merge commit and the ref it was reachable from.
A reader can then tell an early merge from an ordinary push without inferring it
from which fields happen to be populated. This is the half of issue 1021's
required behaviour that the existing flag does not supply.

**`merge-step` is satisfied from that record.** A step whose push receipt
carries an adopted merge is completed from the record instead of by asking
GitHub to merge again, and the receipt names which mechanism satisfied it. Every
other gate `merge-step` applies stays in place, and an incomplete or unverified
adoption still refuses.

The two halves are one decision. Adopting at push without teaching `merge-step`
to read it leaves the run stuck one phase later, and teaching `merge-step` to
read a record nothing writes is not a change at all.

## Alternatives

- **A separate `adopt-early-merge` transition.** A new subcommand recording the
  early merge as its own ledger event, before `done push`. The cleanest audit
  trail: one event, one name, nothing overloaded. Rejected on surface. It adds a
  subcommand, a state key, a verify replay branch and one more GitHub read, and
  the measured comparison in the run's design record puts it behind adoption at
  push on all three of transitions touched, new command surface and added
  network reads. The audit-trail advantage it buys is available for the cost of
  one receipt field.
- **Relax `merge-step` alone and leave `done push` as it is.** The smallest
  diff, and the closest fit to issue 923's precedent, since `merge-step` is
  where the base disagreement actually surfaces. Rejected because it does not
  reach the dead end: `done push` runs first and still refuses, so the run never
  gets to `merge-step`. Documented on its own terms it also fails the
  explicitness requirement, because the push receipt would record the early
  merge only as an inference.
- **Keep refusing and document the manual recovery.** Honest, and it is what
  happens today. Rejected because the recovery is a force-push over a published
  ref, which every other rule in this loop forbids, and because the evidence the
  refusal protects survives an early merge intact: each head was still the exact
  head of its pull request when it merged.

## Consequences

A gate that used to refuse a class of GitHub-reported state now admits part of
it, so the two hard gates carry weight they did not carry before. A head
mismatch and an unreachable merge commit are the rewrite cases, and each has to
keep refusing for the adoption to be safe rather than merely convenient. The
run's risk register names both, and its audit rounds enumerate them.

One recorded fact now stands in for an action. `merge-step` completing without a
merge is correct only while the record it reads is complete and GitHub-verified,
so the check that the adoption is whole is doing the work the second merge used
to do.

Stack discipline is unchanged. The loop still brings the stack down in the
integrate phase, and this decision takes no view on whether merging a stacked
pull request early is good practice. It makes the run survive a merge it did not
perform.

The gate ships inside the artefact it gates, so none of this governs the run that
writes it. A step pull request merged early during this delivery still takes the
manual recovery, and the run's own report says so rather than implying otherwise.
