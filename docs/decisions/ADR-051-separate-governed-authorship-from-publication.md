# ADR-051: Separate governed authorship from publication

## Status

Accepted, 2026-08-30. Extends
[ADR-016](ADR-016-attribute-governed-agent-work-to-shoggoth.md) and
[ADR-018](ADR-018-bind-merged-authorship-to-the-integration-receipt.md).

## Context

ADR-016 correctly made the contributing actor the author and rejected runtime
hosts as authors. It also required a Shoggoth-authored run to use the Shoggoth
signer and GitHub account. GitHub later stopped accepting new commits whose
committer is `shoggoth@wildcat.finance`, while the registered key continued to
verify locally. Signing the same trees with another registered key did not
change the refusal. Keeping Shoggoth as author and making Laurence Day the
committer and signer did: GitHub accepted the push and reported the commit
verified.

The earlier rule coupled four distinct roles. Git records an author and a
committer. A signature belongs to the commit object produced by the committer.
The repository account carrying a branch or opening a pull request is another
observable identity. None of those fields changes who contributed the work.

## Decision

Authorship and publication are recorded separately. Shoggoth-authored work
keeps `Shoggoth <shoggoth@wildcat.finance>` in the author fields. When a person
with authority over the publication explicitly takes the publication role,
that person uses their own committer identity, signing key and repository
account. A runtime host is accepted in none of those roles.

Fiat reads the author and committer from the exact local commit and rejects a
known runtime host in either field. At the push boundary it uses the one GitHub
commit response that already supplies signature verification to record two
separate attribution records: the author and the committer. Each carries the
matched account or explicit null, the name and a digest of the lowercased
address; neither stores the address. Existing author-only receipts remain
readable as the evidence their earlier controller recorded.

The record does not infer the account that pushed the Git ref, because the
commits endpoint does not answer that question. It also does not turn an
observed committer or an operator-supplied account into proof that the person
had authority. The user's instruction or repository policy supplies that
authority, and issue #893 owns its enforceable repository gate.

The final integration continuity check remains about authorship. It tests the
primary author recorded for each pushed commit and does not fold the separately
recorded committer into that view. Publishing Shoggoth's work does not make the
publisher a contributor whose identity a later squash must carry.

## Alternatives

- **Wait for the Shoggoth account to recover.** This leaves delivery dependent
  on an external support timeline and provides no route when another platform
  rejects an otherwise correct publication identity.
- **Reauthor the work as the publisher.** This makes the GitHub badge green by
  erasing the contributing actor, which is the error ADR-016 exists to stop.
- **Treat any locally valid signature as sufficient.** GitHub's repository rule
  evaluates its own account, email and key relation. Local validity is useful
  evidence and not a substitute for the exact remote verdict.
- **Add a controller allow-list now.** A stored login would still be an operator
  declaration rather than proof of authority, while issue #893 already owns
  the repository-wide author and approval policy.

## Consequences

Delivery can continue when the authored identity is sound and the platform
requires a different authorised committer. The commit and Fiat receipt keep
the split visible, so publication does not silently become authorship.

New receipts are slightly larger and reject a missing, malformed or known-host
committer before advancing. The existing one-request-per-commit path remains:
author, committer and verification come from the same response. Historical
receipts do not acquire evidence they never recorded.

An explicit human publication instruction remains necessary. If nobody with
authority can provide a repository-valid signing and account route, the work
still stops before publication and hands off the exact branch or patch.
