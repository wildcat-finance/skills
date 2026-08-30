# ADR-016: Attribute governed agent work to Shoggoth

## Status

Accepted, 2026-08-23. Supersedes the communication-only authorship boundary in
[ADR-011](ADR-011-load-one-shoggoth-identity-contract.md).

The publication handoff paragraph is superseded by
[ADR-051](ADR-051-separate-governed-authorship-from-publication.md). The
authorship decision remains in force.

## Context

Claude Code cloud work reached the repository with commits attributed to
`claude`, pull requests attributed to `app/claude`, and generated-by footers.
Those fields described the host that ran the work, while the work itself used
the Shoggoth's domain and phase skills, Fiat controller, provenance trailers,
and evidence gates. GitHub consequently treated a transport identity as a
repository contributor.

The Interceptor has the same problem even when a particular loop selects no
skill: the harness is itself the Shoggoth's external operating form. Human
contributors are different. Their judgement and work remain theirs, with
Shoggoth provenance or sign-off added rather than substituted.

## Decision

Authorship follows the contributing actor, not the runtime host. Agent-produced
work contributed by Shoggoth that invokes a Wildcat domain or phase skill is
authored by Shoggoth. All Interceptor-produced work is authored by Shoggoth.
Runtime hosts and models are execution metadata, not Git authors, co-authors,
pull-request bylines, or generated-by footers for that governed work.

A human contributor retains human authorship, including when a host helps them
run Fiat. Their commits use their own Git author and valid signing identity,
and their pull request uses their own GitHub account. Shoggoth provenance and
sign-off supplement that authorship. They do not call for the Shoggoth private
signing key or GitHub account to be requested, copied, uploaded or provisioned.
Work outside the Interceptor that invokes no Wildcat domain or phase skill may
retain ordinary Claude, Codex, or other host attribution.

Fiat rejects known host identities in its exact local commit range and in the
pull request it receipts. When Shoggoth is the contributing actor, a cloud run
that cannot use the Shoggoth signer and GitHub account stops before publication
and hands its exact branch or patch to a Shoggoth environment. When a human is
the contributing actor, the run instead signs and publishes as that human; it
never solves missing access by asking for Shoggoth credentials. The Interceptor
applies the Shoggoth check before its sanctioned pull-request wrapper publishes
a branch.

## Alternatives

- **Keep host authorship and add only `Wildcat-Origin`.** This preserves the
  platform defaults, but GitHub continues to award contributor identity to the
  transport while the provenance marker says the work came from Shoggoth.
- **Rewrite historical commits and pull requests.** This would make the past
  display agree, but it would destroy signed history and cannot change an
  existing pull request's opening account. The rule is prospective.
- **Make Shoggoth replace every human contributor.** This would produce one
  tidy identity at the cost of erasing the people whose judgement and work
  grew the collective.
- **Put the rule only in local Git configuration.** That works on one machine
  but does not travel to cloud sessions, contributor machines, installations,
  or the Interceptor.

## Consequences

Governed agent work has one durable author across Claude, Codex, and later
hosts. Human contributors remain visible. Host diagnostics can still record
the runtime privately without turning it into repository authorship.

Cloud work contributed by Shoggoth needs a publication handoff while the
Shoggoth private key remains local. External human work instead needs an
environment that can sign and publish through the human's own identity. Neither
case transfers the Shoggoth key. Fiat and the Interceptor fail closed on the
known host identities they can inspect; prose still owns unfamiliar future host
names until the mechanical set is extended. Historical attribution remains
unchanged.
