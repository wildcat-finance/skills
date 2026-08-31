# ADR-001: one disposition per scoped item, and a ratio that cannot be gamed

## Status

Accepted, 2026-08-31. Raised by [the study](../dokimasia-study.md) and the
frontend UAT assessment it carries forward.

## Context

A release is declared tested because a spreadsheet says so. The spreadsheet is
a list of rows a person wrote. It has no denominator, so nothing in it can
distinguish a route that passed from a route nobody thought of. Adding rows
does not close that gap; it enlarges the numerator of a fraction whose
denominator was never written down.

Two things go wrong with a coverage number, and both are quiet. The
denominator shrinks, so the number rises while less is examined. Or an item is
marked covered because a test exists, without anyone having written down what
the test was supposed to prove.

## Decision

Every scoped item carries exactly one disposition, drawn from a closed set:

| Disposition | What it asserts |
| --- | --- |
| `covered` | a reviewed oracle exists and something is held to it |
| `manual` | a person owns it, and the reason it is not automated is recorded |
| `excluded` | it is out of scope, and the reason is recorded |

Two dispositions on one item refuse. Zero refuse. An item whose disposition
names an oracle that is absent refuses. A disposition recorded against an
inventory digest that has since moved is stale and refuses rather than being
carried forward.

The closure ratio is scoped items carrying a disposition, over scoped items,
and its numerator and denominator are emitted as separate fields beside it. One
is the only passing value, and it means nothing is unaccounted for. It does not
mean anything passed.

A person owns every disposition. An agent may propose one. It may never mark an
item covered on its own, and no code path exists that would let it.

## Alternatives

**A percentage over automated tests.** Familiar, and already available from any
coverage tool. It answers a different question: how much of the code a test
executed, not whether anybody decided what the code should do. An item with no
oracle and a passing line-coverage number reads as covered.

**A four-state disposition with a partial value.** Tempting, because reviewers
want to record work in progress. It makes the ratio unreadable: two people with
the same partial set report different numbers depending on how they round, and
the state becomes where uncomfortable items go to be forgotten.

**No exclusions at all.** Honest in principle and unusable in practice.
Accessibility, legal copy and subjective visual judgement belong to people, and
a model that cannot say so forces reviewers to lie in one of the other two
states.

## Consequences

The ratio is boring by construction. It reaches one when the work of deciding
is done, and it says nothing about quality, so nobody can present it as a
quality number without being caught by its own definition.

Every excluded item carries a reason, so the exclusions are a readable list
rather than a silent shrinkage. Reviewing that list is how the denominator is
audited.

The vocabulary is now expensive to change. A fifth state, a renamed state, or a
changed meaning for an existing one alters every recorded scrutiny, so it needs
its own decision record and a stated migration for the records already written.
