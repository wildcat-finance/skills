# ADR-021: Land a rewritten stack from the original commits

## Status

Accepted, 2026-08-24. Narrowed on 2026-08-30 for
[skills#923](https://github.com/wildcat-finance/skills/issues/923). Originally
recorded for [skills#540](https://github.com/wildcat-finance/skills/issues/540).
Depends on
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

The controller checks every waiting step at the first subsequent `merge-step`.
Equality needs no graph query. For unequal tips it asks native
`git merge-base --is-ancestor <recorded> <tip>` with replacement objects,
inherited `GIT_*` substitution, lazy fetch, and prompts disabled. Status 0
admits topology only: the branch still contains the push receipt's head. That
step later earns fresh local signature, provenance, GitHub verification,
author, and committer evidence over its complete live range in the merge
receipt's `effective_push`, without changing the original push receipt.

Status 1 refuses because the waiting history no longer contains the recorded
head. An unavailable object, failed process, timeout, output cap, or any other
status refuses as unknown. Both paths name the branch and exact commits, but
neither attributes a cause the controller did not observe. When separate
evidence establishes GitHub's native-stack rewrite, the original recovery in
this ADR still applies. Importing GitHub's public key to satisfy the signature
check remains refused: it would make the check pass by removing what the check
establishes.

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
- **Re-receipt every branch after a forward extension.** Rejected because it
  would rewrite append-only push evidence after the run has entered
  integration and would make the earlier reviewed range disappear.
- **Repeat the complete push preflight before every merge.** Rejected because
  it duplicates the merge receipt's existing full-range verification while
  still needing a separate topology rule for waiting branches.
- **Keep permanent equality.** Rejected because a signed forward repair can
  preserve every receipted commit, as issue #923 demonstrated. Equality would
  continue to classify that valid history as a rewrite.

## Consequences

A genuine rewritten stack costs one extra pull request and a set of
superseded-closes instead of fourteen silently re-signed commits. The
merge-step receipt trail for that stack stays honest by never being written;
the integration pull request carries the evidence instead. A strict descendant
does not take that recovery merely because its tip differs. It may proceed, but
only its later complete-range `effective_push` proves current signatures,
provenance, GitHub verification, author, and committer identity.
`push-discipline.md` describes both relations, and the controller carries the
refusal so the rule holds even when the document is not read.
