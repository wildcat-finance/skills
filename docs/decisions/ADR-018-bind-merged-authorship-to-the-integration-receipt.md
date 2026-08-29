# ADR-018: Bind merged authorship to the integration receipt

## Status

Accepted, 2026-08-24. Extends
[ADR-016](ADR-016-attribute-governed-agent-work-to-shoggoth.md), which settled
who the author is. This settles what the record establishes about the author
who reached the default branch.

The decision is recorded before the code that carries it. Steps 2 and 3 of the
issue 466 runbook implement it, so the present tense below describes what was
decided rather than what the controller already does. Fiat v5.13.1 records no
attribution and checks nothing at the merge; `fiat-v5.15.1` is the generation
that carries this record.

Numbered 018 rather than 017. This run committed it as ADR-017 in step 1, and
the Sapheneia audit-record run took that number on `main` before this run
reached step 4.

## Context

ADR-016 gave Fiat a deny list. The controller rejects a known runtime host as
commit author, co-author, pull-request account or generated-by byline, and it
reads the author identity only to run that check. Nothing is recorded about the
identity that passed, and nothing compares the identity on the branch with the
identity on the base after the merge.

The repository publishes a claim that depends on both. `README.md` tells a
contributor that a completed job merged with their authorship intact adds them
to the contributor list automatically. The antecedent is the part Fiat could
establish and does not.

The gap is not theoretical. The repository permits merge commits, squash merges
and rebase merges. A squash replaces the reviewed range with one new commit and
a rebase rewrites every SHA, so under either the commits Fiat verified and
receipted are not the commits the base carries. GitHub also returns `author` as
`null` for a commit whose author email it cannot match to an account, which is
the ordinary outcome for a contributor whose commit email is not on their
GitHub account. Both cases end with a run recorded as complete and a
contributor absent, with nothing in the record saying which happened.

## Decision

Two things, both prospective.

**A recorded attribution is a public login and a digest, never an address.**
The push receipt stores, per verified commit, the GitHub account the commit is
linked to or an explicit `null`, the author name, and the SHA-256 digest of the
lowercased author email. The account is the identity and the
digest corroborates it: [skills#515](https://github.com/wildcat-finance/skills/issues/515)
found one person holding two author emails and one GitHub account, so two
digests can name one contributor while one account cannot name two. The digest
carries the comparison only where the account is `null` and there is nothing
else to compare. It keeps an account address out of `.hexaemeron`; a reviewer
holding the public repository can recompute it, and a copy of the state file
discloses no address.

**The claim is bound at the receipt, not by gating the merge method.**
`done integrate` requires every recorded identity to remain attributable from
the recorded merge commit, by one of two mechanisms: the commit that carried it
is an ancestor of the merge, or the identity appears as author or
`Co-authored-by` of the merge commit itself. It records which mechanism held,
and refuses the receipt when neither does. Fiat does not read repository merge
settings and does not require a particular method. The `integrate` directive
names the method that preserves attribution, so the operator is told before the
merge rather than refused after it.

## Alternatives

- **Refuse to run unless merge commits are permitted.** Settings say what is
  possible, not what a maintainer clicked, and a contributor cannot change the
  settings of a repository they do not administer.
- **Store the author name and email and compare them literally.** The simplest
  comparison, and it writes an account address into untracked local state that
  gets copied, archived and read by later commands. A `users.noreply` address is
  not less private for being obscure.
- **Query the contributors endpoint after the merge and require the login.**
  This looks like the strongest evidence and is the weakest. That list is
  computed asynchronously and cached, so a query immediately after a merge
  reports the state before it, and a gate that fails on timing gets bypassed.
- **Leave the README claim and record nothing.** The claim then rests on a
  condition the repository asserts and never checks, which is the fault this
  record exists to remove.

## Consequences

A completed run states which identities its work published under and whether
the base still carries them. A maintainer can answer both from the ledger
rather than from a commit log and a guess.

Fiat stops a false claim rather than a bad merge. The refusal arrives after the
merge has happened, so recovery is a halt with the blocker recorded and a
maintainer decision, not a prevented action. That is the cost of not gating the
merge method, and it is deliberate: a gate Fiat cannot enforce everywhere is
worse than a claim it refuses to make.

An unlinked author is recorded as unlinked rather than treated as a failure.
Whether an email is matched to an account is GitHub's to decide and the
contributor's to configure, so the receipt reports it and the published prose
names it as a condition the repository does not control.

Historical receipts keep no attribution container, and reading one is optional
everywhere it is read. Extending the known-host set stays prose work under
ADR-016; this record adds no name to it.
