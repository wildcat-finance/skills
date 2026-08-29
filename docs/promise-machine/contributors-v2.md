# Contributor ranking, v2

The contract for `scripts/contributors.py`. It states what a successful run
establishes, what it does not, and what makes it refuse.

## Subject

A ranked list of the human contributors resolved from the GitHub contributors
endpoint for `wildcat-finance/skills` and the human authors of merged pull
requests in `wildcat-finance/shoggoth-wave-atlas`. Rendered into
`CONTRIBUTORS.md` and the thanks block in `README.md` from one computation, so
the two cannot disagree.

## What a successful run establishes

That every Skills contributor row and every merged Wave Atlas pull-request
author returned by GitHub was placed in exactly one of three outcomes: ranked,
excluded with a named reason, or a refusal. That each ranked login is a
syntactically valid GitHub login, is absent from the runtime-host set that
`hexctl.py` declares, is not the Shoggoth's account and is not the repository
owner. A login qualifies through either a resolved Skills commit with a bounded
non-host authorship sample or an authored, merged Wave Atlas pull request. The
order is Skills commits descending, then merged pull requests across both
repositories descending, then login ascending. Both artefacts on disk match
that computation byte for byte when `--check` exits zero.

## Evidence classes

`checked` for the classification, the ordering, the login grammar, the host-set
parity against `hexctl.py`, and the artefact comparison. `recorded` for the API
responses the run read and the per-identity classification lines it emitted.

## Boundary

The run does not establish that the counts are a fair measure of contribution,
that a commit carried judgement, who wrote which line, who else worked on a
pull request, or anything about a person beyond the account GitHub attached to
the evidence. The commit column counts Skills commits only. A Wave Atlas
pull-request author is the account that opened the PR, not every commit author,
reviewer or collaborator. The run does not establish that GitHub's account
resolution is correct, only that it was used. It does not detect a merge that
discarded commit authorship before the commit reached the Skills default branch,
which reduces a count with no local trace; that gap belongs to issue #466. The
Skills commit-authorship corroboration samples at most twenty commits per
account and reports the sample size rather than implying completeness.

## Authorises

Writing `CONTRIBUTORS.md` and the marked region of `README.md`, and nothing
outside those two targets. It authorises no push, no merge and no other
repository mutation; the daily workflow performs those separately under its own
declared permissions.

## Refuses

An account type other than `User` or `Bot`. A `Bot` absent from the declared
host set, because a host name that does not exist yet cannot be classified and
must not be ranked. A merged pull request without a classifiable author. A login
failing the GitHub login grammar. A repository argument carrying query syntax
or a duplicate repository source. Any API read that fails, including a rate
limit, which it names along with whether a token would help. A host set that has
diverged from `hexctl.py`'s declaration, in either direction. An excluded login
reaching the ranked output. A `README.md` that is absent or not UTF-8. A
contributors, closed-pull-request or closed-issue read that would silently
truncate.

## Recovery

Read the stop message, which names the identity or field at fault. For an
unknown host identity, extend the mechanical set in `hexctl.py` and the copy in
`scripts/contributors.py` together, which the parity test enforces. For a rate
limit, set `GITHUB_TOKEN` or wait for the reset the message names. For a stale
artefact, rerun with `--write`. The generator never repairs an input.
