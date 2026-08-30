# ADR-058: Require base-owned identity checks and human review

## Status

Accepted, 2026-08-30. Extends
[ADR-016](ADR-016-attribute-governed-agent-work-to-shoggoth.md) and
[ADR-052](ADR-052-separate-governed-authorship-from-publication.md).

## Context

GitHub's signed-commit rule verifies a signature without deciding whether the
author or committer fields name the contributing actor. A cloud host can sign
with an environment-managed key, put its own identity in both fields, and
receive a green badge. Fiat rejects that attribution inside its own runs, but
the protected branch does not require contributors to use Fiat. The branch
also requires no approving review, so the pull-request author can be the sole
party to the merge.

A normal pull-request workflow is not sufficient policy authority: the
candidate merge tree can change the workflow or script that judges it. A
`pull_request_target` workflow receives trusted base bytes but becomes unsafe
if it checks out and executes the candidate.

## Decision

Run one unconditional base-context Actions job named `identity` for every pull
request to `main`. Check out the exact base SHA as policy, fetch the proposed
history into a separate bare object database, and execute only the base-owned
identity script. Never check out, import, build, or install candidate bytes in
that privileged job. Keep contents read-only and grant only the additional
commit-status write permission needed to publish the result against the
validated event head. Pass event values through environment variables rather
than shell interpolation.

The script checks every commit outside the exact base. It refuses a known
runtime host as author, committer, co-author, generated-by attribution, or
pull-request login; malformed or unreadable identity data also refuses. It
reuses the host classification already shared by Fiat and the contributor
pipeline. Shoggoth authorship must use the exact canonical identity and
provenance trailers. Human authors remain allowed and are not reauthored as
Shoggoth.

`pull_request_target` attaches its native job to the base branch SHA, while a
required check must pass on the latest pull-request SHA. The job therefore
posts `identity` pending against the validated event head before fallible work,
then posts success only when the evaluation step succeeds. A failure posts
failure where possible; cancellation or publication failure leaves pending.

Merge the base-owned workflow before requiring its context. Then use a signed
canary to prove that GitHub Actions publishes `identity` on the exact
pull-request head under integration `15368`. Only after that proof may the live
required-CI ruleset add `identity` alongside strict `invariants` and `plugins`.

Separately, raise the protected branch's required approving review count from
zero to one. One approving review is required. Preserve every other rule and
add no bypass actor. Approval does
not prove authorship; it prevents one party from being the only party to the
merge.

## Alternatives

- Treat any verified signature as authorship evidence. This repeats the false
  inference demonstrated by issue #893.
- Keep the check only inside Fiat. This leaves direct pull requests outside the
  controller unguarded.
- Execute the candidate's copy of the identity script. The proposed change can
  make its own policy return success.
- Check out the candidate under `pull_request_target`. The privileged workflow
  would expose the repository to candidate-controlled hooks, imports, builds,
  or dependencies.
- Require an explicit account allowlist. The repository accepts external human
  contributors, and the present evidence supports rejecting known hosts rather
  than declaring a closed list of authorised people.
- Require two reviews or code-owner review. No evidence in this issue justifies
  that broader governance change.

## Consequences

Signed commits and authorship become separate required signals. A pull request
cannot pass when any inspected identity surface names a known runtime host, and
the candidate cannot rewrite the deciding policy. An independent approving
review is required before merge.

The policy remains prospective. An unfamiliar future host name is not silently
reclassified as a known runtime; the mechanical set must be extended when
evidence identifies it. A green result establishes only that the bounded
known-host checks passed on the stated commits. It does not prove publication
authority, contributor intent, or the correctness of the change.

Bootstrap requires one signed workflow pull request and one signed canary
before live enforcement. If the explicit status is absent from the exact
canary head, comes from the wrong source, or lacks its Actions run link, the
required-check update stops.
