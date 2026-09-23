# Decision: Ice the approving-review requirement

## Status

Accepted, 2026-09-23. Numberless until the merge that lands it, under the
draft path [ADR-077](../ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md)
set out. It suspends one clause of
[ADR-058](../ADR-058-require-base-owned-identity-and-human-review.md), the
requirement for one approving review before merge, and leaves the rest of
ADR-058 and all of
[ADR-099](../ADR-099-accept-any-validly-signed-authorship.md) in force. Neither
record is edited.

## Context

ADR-058 raised the protected branch's required approving review count from zero
to one. ADR-099 withdrew the runtime-host ban and states that this review
requirement "is not withdrawn".

On 2026-09-23 the branch protection on `main` sets no required pull-request
reviews (`required_pull_request_reviews` is null). Its only required status
check is `invariants`. The one ruleset, "Required CI", is in `evaluate` mode.
GitHub therefore enforces no review, while the recorded policy still asks for
one.

The same day, Dr Laurence E. Day (laurenceday), Wildcat Labs, ruled that the
repository does not need independent reviewer permissions at this stage, and
that the requirement should be iced and re-enabled when appropriate.

## Decision

Ice the approving-review requirement. A pull request to `main` needs no
approving review before merge. Agents do not hold a pull request for a review
and do not report a missing review as a blocker.

Everything else stays: signed commits, the required `invariants` check, the
commit gate and each queue's issue-body contract. Registry and record fields
that name "the reviewer of the pull request" describe a role and gate nothing.

Re-enabling is a maintainer decision, recorded in a new decision record that
lifts this one. That record then sets the branch protection's required
approving review count back to one.

## Alternatives

- Leave ADR-058's clause standing. The recorded policy would keep disagreeing
  with the branch protection, and agents following the record would wait for a
  review nobody is assigned to give.
- Edit ADR-058 or ADR-099. Both are evidence of the policy they set, and
  `tests/test_commit_identity.py` quotes ADR-058's review sentence.

## Consequences

A pull-request author can be the only party to a merge, as the live branch
protection already allowed. Approval never proved authorship. Signed commits
and the required checks remain the merge signals.
