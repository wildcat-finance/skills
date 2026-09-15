# Decision: Accept any validly signed authorship

Stable identity: `adr/accept-any-validly-signed-authorship`.

## Status

Proposed, 2026-09-06. Supersedes the authorship policy in
[ADR-016](../ADR-016-attribute-governed-agent-work-to-shoggoth.md) and the
host-identity policy in
[ADR-058](../ADR-058-require-base-owned-identity-and-human-review.md). Those
records remain unchanged as historical evidence. ADR-058's separate
requirement for one approving review remains in force.

## Context

The repository currently treats Shoggoth attribution and the absence of a
known runtime host as evidence required in addition to a valid commit
signature. Fiat requires two Shoggoth provenance trailers, rejects runtime
hosts in authorship and publication fields, and records those checks in its
receipts. A base-owned GitHub Actions job repeats the host-identity policy for
pull requests to `main`.

Those checks conflate three distinct questions. Signature evidence establishes
that a named commit passed the verifier used at that transition. Authorship
records who is named as contributing the work. Publication authority decides
who may change a repository or its hosted settings. None establishes either of
the other two.

Authenticated GitHub operations may also arrive through local tooling or a
connected interface. When either route returns the exact repository, object,
verification, pull-request, or mutation fields a transition requires, the
evidence has the same standing. An unavailable or incomplete read remains
unknown and does not pass.

## Decision

Accept any author, committer, co-author, pull-request opener, or byline when the
commit-bearing transition has its required valid-signature evidence. Neither
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` nor
`Wildcat-Origin: shoggoth` is mandatory.

Local Fiat-created commits continue to require a successful `git
verify-commit`. Pushed and host-created commits continue to require an exact
platform readback with `verified: true` and `reason: valid`. These checks say
nothing about the signer's authorship or publication authority. Repository
instructions and explicit authority still govern publication separately.

Treat exact authenticated GitHub evidence from a connected interface as
equivalent to evidence returned by local authenticated tooling. Do not infer a
successful or empty result when either route cannot return the required
fields.

Retire the base-owned `identity` job and its host-classification checker after
the live ruleset no longer requires that status. Once host attribution is
permitted, the job has no remaining identity decision to enforce. Keep the
separate approving-review requirement and every unrelated branch rule.

Keep human-only contributor ranking separate from commit admission. Excluding
a non-human account from `CONTRIBUTORS.md` does not forbid that account from
validly signed authorship or publication where it has authority.

## Alternatives

- **Retain a structural identity job.** This would preserve hardened range and
  grammar parsing, but it would keep a required hosted job with no remaining
  identity claim.
- **Delete signature and identity controls together.** This would be smaller,
  but it would admit unsigned or invalidly signed commits and discard the
  evidence this decision retains.
- **Make the former attribution rules configurable.** This would ease a staged
  migration, but it would preserve withdrawn policy, add persistent state, and
  turn one rule into a mode matrix.
- **Keep mandatory Shoggoth attribution and the runtime-host ban.** This would
  retain consistent collective attribution, but it would continue to reject
  otherwise validly signed contributions for an authorship convention that no
  longer governs admission.

## Consequences

Claude, Fable, Codex, another runtime host, a human, or another account may
appear in authorship and pull-request surfaces without an identity refusal.
Each Shoggoth provenance trailer is optional. Missing or invalid required
signature evidence still stops the relevant transition.

Fiat and hosted policy become transport-neutral: exact authenticated evidence
can come through local or connected GitHub interfaces. Publication still
requires repository authority, and a valid signature does not grant it.

The hosted `identity` workflow, checker, and required status can be removed in
a controlled order, reducing a maintenance and hosted-job surface that no
longer enforces a live promise. Historical records and receipts continue to
describe the policy that applied when they were written.
