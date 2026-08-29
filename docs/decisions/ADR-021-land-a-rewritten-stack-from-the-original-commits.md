# ADR-021: Land a rewritten stack from the original commits

## Status

Accepted, 2026-08-24. Recorded for
[skills#540](https://github.com/wildcat-finance/skills/issues/540). Depends on
[ADR-016](ADR-016-attribute-governed-agent-work-to-shoggoth.md) for why the
Shoggoth signature is the guarantee being protected.

## Context

Fiat builds a delivery as a chain of step branches, each pull request targeting
the branch below, so a reviewer sees one step's diff at a time. GitHub can claim
such a chain as a native stacked pull request set. In that regime it refuses
base changes and the ordinary merge paths, accepts merges only through its
asynchronous endpoint, and on each merge rebases every downstream branch,
re-signing the rewritten commits with its web-flow key.

The delivery for issue #515 met this. After three of five steps had merged,
fourteen of the twenty commits on the run branch carried GitHub's key rather
than the Shoggoth key. GitHub reported every one `verified: true`, because the
key is its own, so the pull request view looked healthy while the local signature, the thing
this repository's provenance model rests on, was gone.
The controller's signature check refused the next receipt, which was correct
and far too late.

## Decision

The step chain remains the review topology: one branch per step, one pull
request per step, stacked. It is no longer the landing topology when GitHub has
claimed it. A run whose stack has been rewritten lands from a branch holding the
original unrebased commits, through one pull request into the base; the final
step's pushed head already carries the whole stack as one linear signed chain.
The stacked pull requests are closed as superseded with a pointer to where the
same commits landed, so the review record survives.

The controller detects the rewrite at the first `merge-step` after it happens,
by comparing every waiting step's remote tip against the head its push receipt
names, and refuses with the cause and the recovery named. Importing GitHub's
public key to satisfy the signature check is refused in the message itself: it
would make the check pass by removing what the check establishes.

## Alternatives

- **Accept GitHub's web-flow key as a valid signer.** Every rewritten commit
  verifies on GitHub, so this is one frozenset away. Rejected because the
  guarantee would become "GitHub processed this", which is true of any commit
  GitHub hosts, and the Shoggoth signature would stop meaning anything.
- **Refuse the stacked topology entirely and build steps as siblings of the run
  branch from the start.** Rejected for now: the stacked diff per step is the
  reviewable unit, and GitHub only interferes at merge time. Revisit if GitHub
  begins rewriting branches before merge.
- **Detect enrolment at push time and stop earlier still.** Attractive, but the
  signal GitHub exposes for "this pull request is part of a stack" is not a
  documented stable field. The merge-step check is later but reads only facts
  the controller already trusts: remote tips and its own receipts.

## Consequences

A rewritten stack costs one extra pull request and a set of superseded-closes
instead of fourteen silently re-signed commits. The merge-step receipt trail for
a rewritten stack stays honest by never being written; the integration pull
request carries the evidence instead. `push-discipline.md` describes both
regimes, and the controller carries the refusal so the rule holds even when the
document is not read.
