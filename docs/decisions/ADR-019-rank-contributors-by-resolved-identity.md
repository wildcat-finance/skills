# ADR-019: Rank contributors by resolved identity, not by provenance trailer

## Status

Accepted, 2026-08-24; amended 2026-08-28 to include merged pull-request authors
from Shoggoth Wave Atlas. Numbered 019, having been renumbered twice while two
concurrent deliveries landed ahead of it. 017 went to
[ADR-017](ADR-017-gate-durable-agent-prose.md), which gates durable agent prose
before publication. 018 went to
[ADR-018](ADR-018-bind-merged-authorship-to-the-integration-receipt.md), the
record for issue #466. Both are on the default branch, so both are linked here
rather than named in the abstract. Depends on
[ADR-016](ADR-016-attribute-governed-agent-work-to-shoggoth.md) for what an
agent identity is, and consumes the authorship evidence ADR-018 binds at
integration time.

## Context

`README.md` told a prospective contributor that a completed job leaves them in
this repository's contributor list. That was true only of GitHub's Insights
graph: no `CONTRIBUTORS.md` existed and nothing generated one.

Building the list required deciding which identities count. The repository
already marks agent work with a `Wildcat-Origin: shoggoth` trailer, so filtering
on that trailer was the obvious approach. Measured against `main` at `dd23413`,
across 718 non-merge commits, it does not work:

- Every commit by both of the repository's external human contributors carries
  `Wildcat-Origin: shoggoth`, because those contributors ran Fiat. Excluding
  trailer-bearing commits removes exactly the people the list exists to name and
  produces an empty file.
- 23 of 197 commits authored by `Claude <noreply@anthropic.com>` carry no
  `Wildcat-Origin` trailer at all, so trailer absence does not imply a human
  author. Filtering on absence ranks a runtime host.

The trailer records which tool performed the work. It does not record who
decided it. Those are different questions and only the second one is being
asked.

Identity has its own difficulty. One contributor appears in `git log` as two
people, "Kethic" and "Dave Coleman", under two email addresses, split 21 and 8.
GitHub's contributors endpoint resolves both to one account with 29. No
hand-maintained alias table produces that without someone remembering to
maintain it.

## Decision

Contributor ranking is keyed on the GitHub login that the contributors endpoint
resolves for a commit author, not on any trailer and not on a raw author email.

Exclusion is by identity, in three named categories, each carrying its own
reason in the output:

1. Runtime hosts, from the mechanical set ADR-016 names and `hexctl.py` holds.
   A copy of that set lives in `scripts/contributors.py` and a test fails when
   the two diverge or when a fourth set appears that the generator does not
   account for.
2. The Shoggoth's own account. ADR-016 makes it the author of governed agent
   work, so it is a legitimate contributor in GitHub's sense and still not a
   person who helped. It is deliberately not in the runtime-host set: a host
   identity is a transport that should never have been an author, whereas this
   one should.
3. The repository owner, at the Creator's instruction.

An identity matching none of these and not resolvable as a human account stops
the run by name rather than being ranked. ADR-016 records that the mechanical
set cannot cover host names that do not exist yet, and ranking an unrecognised
one would put a runtime in a file that thanks people.

Ranking is merged commits, then merged pull requests as tie-break, then login,
so equal counts order identically on every run and a refresh that changed
nothing produces no diff.

The commit dimension remains the resolved commit count from
`wildcat-finance/skills`. The merged-pull-request dimension combines that
repository with `wildcat-finance/shoggoth-wave-atlas`. A human account that
authored a merged Wave Atlas pull request qualifies even when it has no Skills
commit, because the Atlas is itself a contribution surface for this project.
This is evidence about the account that opened the pull request. It does not
attribute every commit, review or collaboration on that pull request to the
opener.

## Alternatives

- **Filter on `Wildcat-Origin`.** Rejected on the counts above: it ranks no
  human and one runtime. Recorded here so a later round does not reopen a
  question this evidence settles.
- **Rank from `git log` with an alias table.** Runs offline and needs no token,
  but a contributor's second email defeats it silently, which is already the
  case in this repository's history.
- **Adopt the `all-contributors` specification and bot.** A convention many
  readers recognise, at the cost of a hand-curated file that nobody updates and
  that knows nothing about ADR-016.
- **Count issue and review activity toward rank.** Out of scope: the request was
  commits and merges. Humans with closed-issue activity and no ranked commits
  are reported separately so they are not silently dropped.

## Consequences

The list names people rather than transports, and one person split across
several email addresses appears once. The generator depends on a network read,
which is what buys identity resolution.

Someone who contributes a merged pull request to Shoggoth Wave Atlas now
appears in the same list. An account with no Skills commits shows zero in that
column, and its merged pull request is the evidence that qualifies it.

Two limits are stated in `CONTRIBUTORS.md` itself rather than left implicit. The
list establishes counts as GitHub resolves them and nothing about how much
judgement a commit carried. And a merge that discards commit authorship reduces
a count with no way for this repository to detect it, which is the gap issue
#466 addresses upstream of here.
