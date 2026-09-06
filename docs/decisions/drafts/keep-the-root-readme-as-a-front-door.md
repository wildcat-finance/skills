# Decision: Keep the root README as a front door

## Status

Accepted, 2026-09-06.

## Context

The root `README.md` had become the catalogue. It listed every member, so the
invitation to contribute sat below three hundred lines of roster; it carried
capability claims the repository could not demonstrate; and its counts were
typed once by whoever last remembered. Nothing could tell a reader which parts
were still true.

Two properties of the page made that inevitable. It was the only public page
anyone maintained, so every new member had to be added to it, and it was
governed by taste alone, so a page that grew past what a newcomer would read
broke no rule.

The repository already had somewhere for the catalogue to live.
`FUTUREPROOFING.md` is the full roster: every member, what it ships today, what
evidence is missing, and what it could become with help. Nothing forced the
root page to duplicate it.

## Decision

The root `README.md` is a front door and not a catalogue. It says what the
collective is, invites contribution, demonstrates what the repository can
reproduce, and then points onward. The complete governed roster lives in
`FUTUREPROOFING.md`, and the front door links to it rather than reproducing it.

The parts of that contract a parser can settle are settled by one, in
`scripts/check_public_front_door.py`, which owns order, budgets, markers and
the agreement between a public claim and its evidence. At this record's date it
holds the introduction to 150 words, the contribution heading and the external
contributor route to the opening 220 words, the whole document to 1,400 words,
and the collective portrait to the region before the title; it refuses a
repeated link target, a second image, a missing retained chirp, and a page that
links every governed skill. The module is the authority on those values, and
they are named here as the shape the decision took rather than as a second copy
to keep current.

Everything the parser cannot settle stays with people. Voice, register and
whether a sentence is worth reading belong to Imprimatur, Vulgate, Brevitas and
human review. The checker never grades prose, and passing it is not a claim
that the page reads well.

A capability claim on the front door is a card, and a card binds one governed
demonstration record by skill id, claim id and record digest. That relation is
`adr/govern-real-data-demonstrations-separately`; this record decides only that
the front door is where such claims are made and what shape the page holding
them takes.

## Alternatives

- **Let the page keep growing, and edit it when somebody complains.** This is
  the state the record replaces. Nothing goes wrong when the page grows except
  that a reader gives up, which is a signal nobody in this repository receives.
- **Split the roster across many pages and leave the root as a link index.** It
  bounds the length, but a link index answers none of the four questions a
  newcomer arrives with, and the capability claims would have moved to pages
  with no checker at all.
- **Generate the whole page from the ledgers.** It would make every claim
  derived and every count current. Rejected because the front door's job is to
  be read by a person deciding whether to spend an afternoon here, and a
  generated page reads as a report. The compromise taken instead is a
  hand-written page with derived numbers inside it: the prose is authored, the
  quantities are not.
- **Keep the contract in review comments rather than in a checker.** Rejected
  because that is what was already happening. Order, length and a stale digest
  are exactly the properties a reviewer stops noticing on the fourth pass.

## Consequences

A member landing in this repository no longer edits the front door. It joins
`FUTUREPROOFING.md` and its own landing page, and the front door's derived
numbers move on their own.

A capability claim now costs a demonstration record. Writing a card for a skill
whose record is missing, downgraded or stale fails the check rather than
standing, so the page can only claim what the repository can reproduce.

The budgets are a real constraint on authors. A section that earns its place
displaces one that no longer does, and the checker will not say which; that
judgement stays with whoever is writing.

The page can still be badly written. Everything this record makes mechanical is
structural, and a front door that satisfies every rule here and reads like
product copy is a failure the checker cannot see.
