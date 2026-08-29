# ADR-009: Four issue queues, told apart by title prefix

## Status

Accepted, 2026-08-21. Superseded by a later numbered record once it stops being
true.

## Context

Work on this marketplace arrives from four different places, and until now only
two of them were legible from an issue title.

A skill's ledger holds one `Next Fiat job`. That target is endogenous: the
system named it, and completing it increments an evolution counter. Those issues
are titled `{skill}-next` and labelled `held-job`.

Separately, a single generated wishlist proposed the top three improvements for
each skill and numbered them one to three. That produced #317 through #334,
titled `{skill}-N` and labelled `wish`. They are exogenous nice-to-haves: no
Fiat loop determined them, and a finished one occasionally spawns a `-4`. The
artefact was one-off, so the set is closed.

The third source is a Fiat run finding work it has no authority to do. The issue
320 run found a resumed Mason still carrying a handle named for issue 318 and
filed #363 rather than widening its own accepted scope. That behaviour is worth
keeping: the run stays inside its packet and the finding survives somewhere
rankable. It had no title convention, so #363 shipped as `fiat — ...` and a
later audit-log finding shipped as a sentence with no owner at all.

The fourth is the same run observing that the system as a whole falls short,
where the shortfall belongs to no single skill and picking one would be a guess.

Two things forced the question now. The queues are being migrated onto issues so
the backlog can eventually be handed to an agent to rank, and a queue is only
rankable when a title says what a thing is and which queue it came from. And
nothing was remembering any of this: the conventions existed in one issue body
and in the conversation that produced it.

## Decision

Four queues, each identified by its title prefix and its label.

| Source | Title prefix | Label |
| --- | --- | --- |
| A ledger's held frontier job | `{skill}-next` | `held-job` |
| The one-off generated wishlist, closed | `{skill}-N` | `wish` |
| A run's skill-specific spin-off | `{skill}-wish` | none |
| A run's system-wide observation | `framework-N` | `observation` |

`{skill}` is the skill's own governed name rather than its plugin's, so Lemma's
is `lemma`. A run's spin-off carries no `wish` label: that label belongs to the
closed numbered set, and reusing it merges two queues that mean different
things.

A `framework-N` issue opens with a line stating that Protasis decides which
skill or skills it upgrades. A system-wide shortfall usually lands in more than
one contract, and the filer is the wrong party to choose.

Fiat's existing prohibition stands: an issue is never created merely to satisfy
the workflow. These conventions say how to title an issue that was worth filing,
not that more should be filed.

## Alternatives

- **Leave it in the issue that proposed it.** That is where it lived, and it
  lost because an issue body is a specification of work not yet done. A reader
  looking for the convention has to know which issue to open, and once that
  issue closes the convention has no home at all.
- **Put it in Fiat's contract now.** Fiat files the issues, so its hard rules
  are a natural home, and it lost for this record because changing a governed
  skill's behaviour needs its own specification and a ledger row. #370 holds
  that work. A record of the decision and an enforcement of it are different
  artefacts, and the record should not wait for the enforcement.
- **Rely on the label descriptions.** All three labels already carry a
  one-line definition, which is genuinely useful and insufficient: an agent
  reads the repository, not the label list, and a label cannot say what a title
  should look like.
- **Retitle the sixteen `{skill}-N` wishes to `{skill}-wish`.** It would leave
  one convention instead of two, and it lost because the ordinal is provenance.
  It says the issue came from the generated wishlist and where it sat in that
  list, which is the only surviving record of why `phylax-2` exists and
  `phylax-4` does not.

## Consequences

A reader can tell from a title alone whether an issue is the system's own next
step, a nice-to-have from a closed list, something a run noticed about a skill,
or something a run noticed about the machinery. That is what makes the backlog
rankable by anything other than the person who filed it.

Two questions stay open and are recorded in #370 rather than guessed here: who
assigns `N` in `framework-N` when two runs file at once, and whether a run's
skill spin-off should carry a label of its own, given that `wish` is taken and
`origin:ai` says only who filed it.

The `wish` label is now closed by decision rather than by accident. Anything
that would have been a wish is a `{skill}-wish` or a `framework-N`, and the
generated artefact that produced the original set is not in this repository, so
the ordinals are the only provenance those sixteen issues have.
