# Contributor ranking, v1

The contract for `scripts/contributors.py`. It states what a successful run
establishes, what it does not, and what makes it refuse.

## Subject

A ranked list of the repository's human contributors, derived from the GitHub
contributors endpoint, merged pull-request counts, and a bounded sample of each
ranked account's commit authorship. Rendered into `CONTRIBUTORS.md` and the
thanks block in `README.md` from one computation, so the two cannot disagree.

## What a successful run establishes

That every contributor row returned by GitHub for the named repository was
placed in exactly one of three outcomes: ranked, excluded with a named reason,
or a refusal. That each ranked login is a syntactically valid GitHub login, is
absent from the runtime-host set that `hexctl.py` declares, is not the
Shoggoth's account, is not the repository owner, and had at least one commit in
a bounded sample whose author was not a runtime host identity. That the order is
merged commits descending, then merged pull requests descending, then login
ascending. And that both artefacts on disk match that computation byte for byte
when `--check` exits zero.

## Evidence classes

`checked` for the classification, the ordering, the login grammar, the host-set
parity against `hexctl.py`, and the artefact comparison. `recorded` for the API
responses the run read and the per-identity classification lines it emitted.

## Boundary

The run does not establish that the counts are a fair measure of contribution,
that a commit carried judgement, who wrote which line, or anything about a
person beyond the account they committed under. It does not establish that
GitHub's own resolution of author emails to accounts is correct, only that it
was used. It does not detect a merge that discarded commit authorship before the
commit reached the default branch, which reduces a count with no local trace;
that gap belongs to issue #466. The commit-authorship corroboration samples at
most twenty commits per account and reports the sample size rather than implying
completeness.

## Authorises

Writing `CONTRIBUTORS.md` and the marked region of `README.md`, and nothing
outside those two targets. It authorises no push, no merge and no other
repository mutation; the weekly workflow performs those separately under its own
declared permissions.

## Refuses

An account type other than `User` or `Bot`. A `Bot` absent from the declared
host set, because a host name that does not exist yet cannot be classified and
must not be ranked. A login failing the GitHub login grammar. A repository
argument carrying query syntax. Any API read that fails, including a rate limit,
which it names along with whether a token would help. A host set that has
diverged from `hexctl.py`'s declaration, in either direction. An excluded login
reaching the ranked output. A `README.md` that is absent or not UTF-8. A
contributors or closed-issue read that would silently truncate.

## Recovery

Read the stop message, which names the identity or field at fault. For an
unknown host identity, extend the mechanical set in `hexctl.py` and the copy in
`scripts/contributors.py` together, which the parity test enforces. For a rate
limit, set `GITHUB_TOKEN` or wait for the reset the message names. For a stale
artefact, rerun with `--write`. The generator never repairs an input.
